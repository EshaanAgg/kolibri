import logging

from le_utils.constants import content_kinds
from sqlalchemy import and_
from sqlalchemy import cast
from sqlalchemy import exists
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import or_
from sqlalchemy import select

from .sqlalchemybridge import Bridge
from kolibri.core.content.apps import KolibriContentConfig
from kolibri.core.content.models import ContentNode
from kolibri.core.content.models import File
from kolibri.core.content.models import LocalFile
from kolibri.core.content.utils.channels import get_mounted_drive_by_id
from kolibri.core.content.utils.content_types_tools import renderable_files_presets
from kolibri.core.content.utils.file_availability import (
    get_available_checksums_from_disk,
)
from kolibri.core.content.utils.file_availability import (
    get_available_checksums_from_remote,
)
from kolibri.core.discovery.models import NetworkLocation

logger = logging.getLogger(__name__)

CONTENT_APP_NAME = KolibriContentConfig.label


def get_channel_annotation_stats(channel_id, checksums=None):
    bridge = Bridge(app_name=CONTENT_APP_NAME)

    ContentNodeTable = bridge.get_table(ContentNode)
    FileTable = bridge.get_table(File)
    LocalFileTable = bridge.get_table(LocalFile)

    if checksums is not None:
        file_table = FileTable.join(
            LocalFileTable,
            and_(
                FileTable.c.local_file_id == LocalFileTable.c.id,
                LocalFileTable.c.id.in_(checksums),
            ),
        )
    else:
        file_table = FileTable.join(
            LocalFileTable, FileTable.c.local_file_id == LocalFileTable.c.id
        )

    contentnode_statement = (
        select([FileTable.c.contentnode_id])
        .select_from(file_table)
        .where(FileTable.c.supplementary == False)  # noqa
        .where(
            or_(*(FileTable.c.preset == preset for preset in renderable_files_presets))
        )
        .where(ContentNodeTable.c.id == FileTable.c.contentnode_id)
    )
    connection = bridge.get_connection()

    # start a transaction

    trans = connection.begin()

    connection.execute(
        ContentNodeTable.update()
        .where(
            and_(
                ContentNodeTable.c.kind != content_kinds.TOPIC,
                ContentNodeTable.c.channel_id == channel_id,
            )
        )
        .values(available=exists(contentnode_statement))
    )

    ContentNodeClass = bridge.get_class(ContentNode)

    node_depth = (
        bridge.session.query(func.max(ContentNodeClass.level))
        .filter_by(channel_id=channel_id)
        .scalar()
    )

    child = ContentNodeTable.alias()

    # Update all leaf ContentNodes to have num_coach_content to 1 or 0
    # Update all leaf ContentNodes to have on_device_resources to 1 or 0
    connection.execute(
        ContentNodeTable.update()
        .where(
            and_(
                # In this channel
                ContentNodeTable.c.channel_id == channel_id,
                # That are not topics
                ContentNodeTable.c.kind != content_kinds.TOPIC,
            )
        )
        .values(
            num_coach_contents=cast(ContentNodeTable.c.coach_content, Integer()),
            on_device_resources=cast(ContentNodeTable.c.available, Integer()),
        )
    )

    # Before starting set availability to False on all topics.
    connection.execute(
        ContentNodeTable.update()
        .where(
            and_(
                # In this channel
                ContentNodeTable.c.channel_id == channel_id,
                # That are topics
                ContentNodeTable.c.kind == content_kinds.TOPIC,
            )
        )
        .values(available=False)
    )

    # Expression to capture all available child nodes of a contentnode
    available_nodes = select([child.c.available]).where(
        and_(
            child.c.available == True,  # noqa
            ContentNodeTable.c.id == child.c.parent_id,
        )
    )

    # Expressions for annotation of coach content

    # Expression that will resolve a boolean value for all the available children
    # of a content node, whereby if they all have coach_content flagged on them, it will be true,
    # but otherwise false.
    # Everything after the select statement should be identical to the available_nodes expression above.
    if bridge.engine.name == "sqlite":
        # Use a min function to simulate an AND.
        coach_content_nodes = select([func.min(child.c.coach_content)]).where(
            and_(
                child.c.available == True,  # noqa
                ContentNodeTable.c.id == child.c.parent_id,
            )
        )
    elif bridge.engine.name == "postgresql":
        # Use the postgres boolean AND operator
        coach_content_nodes = select([func.bool_and(child.c.coach_content)]).where(
            and_(
                child.c.available == True,  # noqa
                ContentNodeTable.c.id == child.c.parent_id,
            )
        )

    # Expression that sums the total number of coach contents for each child node
    # of a contentnode
    coach_content_num = select([func.sum(child.c.num_coach_contents)]).where(
        and_(
            child.c.available == True,  # noqa
            ContentNodeTable.c.id == child.c.parent_id,
        )
    )

    # Expression that sums the total number of on_device_resources for each child node
    # of a contentnode
    on_device_num = select([func.sum(child.c.on_device_resources)]).where(
        and_(
            child.c.available == True,  # noqa
            ContentNodeTable.c.id == child.c.parent_id,
        )
    )

    stats = {}

    # Go from the deepest level to the shallowest
    for level in range(node_depth, 0, -1):

        # Only modify topic availability here
        connection.execute(
            ContentNodeTable.update()
            .where(
                and_(
                    ContentNodeTable.c.level == level - 1,
                    ContentNodeTable.c.channel_id == channel_id,
                    ContentNodeTable.c.kind == content_kinds.TOPIC,
                )
            )
            # Because we have set availability to False on all topics as a starting point
            # we only need to make updates to topics with available children.
            .where(exists(available_nodes))
            .values(
                available=exists(available_nodes),
                coach_content=coach_content_nodes,
                num_coach_contents=coach_content_num,
                on_device_resources=on_device_num,
            )
        )

        level_stats = connection.execute(
            select(
                [
                    ContentNodeTable.c.id,
                    ContentNodeTable.c.coach_content,
                    ContentNodeTable.c.num_coach_contents,
                    ContentNodeTable.c.on_device_resources,
                ]
            ).where(
                and_(
                    ContentNodeTable.c.level == level,
                    ContentNodeTable.c.channel_id == channel_id,
                )
            )
        )

        for stat in level_stats:
            stats[stat[0]] = {
                "coach_content": stat[1],
                "num_coach_contents": stat[2],
                "total_resources": stat[3],
            }

    root_node_stats = connection.execute(
        select(
            [
                ContentNodeTable.c.id,
                ContentNodeTable.c.coach_content,
                ContentNodeTable.c.num_coach_contents,
                ContentNodeTable.c.on_device_resources,
            ]
        ).where(
            and_(
                ContentNodeTable.c.level == 0,
                ContentNodeTable.c.channel_id == channel_id,
            )
        )
    ).fetchone()

    stats[root_node_stats[0]] = {
        "coach_content": root_node_stats[1],
        "num_coach_contents": root_node_stats[2],
        "total_resources": root_node_stats[3],
    }

    # rollback the transaction to undo the temporary annotation
    trans.rollback()

    bridge.end()

    return stats


def get_channel_stats_from_disk(channel_id, drive_id):
    datafolder = get_mounted_drive_by_id(drive_id).datafolder
    checksums = get_available_checksums_from_disk(channel_id, datafolder)
    return get_channel_annotation_stats(channel_id, checksums)


def get_channel_stats_from_peer(channel_id, peer_id):
    network_location = NetworkLocation.objects.values("base_url").get(id=peer_id)
    base_url = network_location["base_url"]
    checksums = get_available_checksums_from_remote(channel_id, base_url)
    return get_channel_annotation_stats(channel_id, checksums)


def get_channel_stats_from_studio(channel_id):
    return get_channel_annotation_stats(channel_id)
