<template>

  <CoachAppBarPage>
    <KPageContainer>
      <ReportsGroupHeader
        :activeTabId="ReportsGroupTabs.MEMBERS"
        :enablePrint="true"
      />
      <KTabsPanel
        :tabsId="REPORTS_GROUP_TABS_ID"
        :activeTabId="ReportsGroupTabs.MEMBERS"
      >
        <ReportsControls @export="exportCSV" />
        <CoreTable :emptyMessage="coachString('learnerListEmptyState')">
          <template #headers>
            <th>{{ coachString('nameLabel') }}</th>
            <th>{{ coachString('avgScoreLabel') }}</th>
            <th>{{ coachString('exercisesCompletedLabel') }}</th>
            <th>{{ coachString('resourcesViewedLabel') }}</th>
            <th>{{ coachString('lastActivityLabel') }}</th>
          </template>
          <template #tbody>
            <transition-group
              tag="tbody"
              name="list"
            >
              <tr
                v-for="tableRow in table"
                :key="tableRow.id"
              >
                <td>
                  <KRouterLink
                    :text="tableRow.name"
                    :to="classRoute('ReportsLearnerReportPage', { learnerId: tableRow.id })"
                    icon="person"
                  />
                </td>
                <td>
                  <Score :value="tableRow.avgScore" />
                </td>
                <td>{{ $formatNumber(tableRow.exercises) }}</td>
                <td>{{ $formatNumber(tableRow.resources) }}</td>
                <td>
                  <ElapsedTime :date="tableRow.lastActivity" />
                </td>
              </tr>
            </transition-group>
          </template>
        </CoreTable>
      </KTabsPanel>
    </KPageContainer>
  </CoachAppBarPage>

</template>


<script>

  import sortBy from 'lodash/sortBy';
  import commonCoach from '../common';
  import { REPORTS_GROUP_TABS_ID, ReportsGroupTabs } from '../../constants/tabsConstants';
  import CoachAppBarPage from '../CoachAppBarPage';
  import CSVExporter from '../../csv/exporter';
  import * as csvFields from '../../csv/fields';
  import ReportsGroupHeader from './ReportsGroupHeader';
  import ReportsControls from './ReportsControls';

  export default {
    name: 'ReportsGroupLearnerListPage',
    components: {
      CoachAppBarPage,
      ReportsGroupHeader,
      ReportsControls,
    },
    mixins: [commonCoach],
    data() {
      return {
        REPORTS_GROUP_TABS_ID,
        ReportsGroupTabs,
      };
    },
    computed: {
      group() {
        return this.groupMap[this.$route.params.groupId];
      },
      groupMembers() {
        return this.groupMap[this.$route.params.groupId].member_ids.map(
          memberId => this.learnerMap[memberId],
        );
      },
      table() {
        const sorted = sortBy(this.groupMembers, ['name']);
        return sorted.map(learner => {
          const examStatuses = this.examStatuses.filter(status => learner.id === status.learner_id);
          const contentStatuses = this.contentStatuses.filter(
            status => learner.id === status.learner_id,
          );
          const augmentedObj = {
            avgScore: this.avgScore(examStatuses),
            lessons: undefined,
            exercises: this.exercisesCompleted(contentStatuses),
            resources: this.resourcesViewed(contentStatuses),
            lastActivity: this.lastActivity(examStatuses, contentStatuses),
          };
          Object.assign(augmentedObj, learner);
          return augmentedObj;
        });
      },
    },
    methods: {
      avgScore(examStatuses) {
        const statuses = examStatuses.filter(status => status.status === this.STATUSES.completed);
        if (!statuses.length) {
          return null;
        }
        return this._.meanBy(statuses, 'score');
      },
      lastActivity(examStatuses, contentStatuses) {
        const statuses = [
          ...examStatuses,
          ...contentStatuses.filter(status => status.status !== this.STATUSES.notStarted),
        ];

        return statuses.length ? this.maxLastActivity(statuses) : null;
      },
      exercisesCompleted(contentStatuses) {
        const statuses = contentStatuses.filter(
          status =>
            this.contentIdIsForExercise(status.content_id) &&
            status.status === this.STATUSES.completed,
        );
        return statuses.length;
      },
      resourcesViewed(contentStatuses) {
        const statuses = contentStatuses.filter(
          status =>
            !this.contentIdIsForExercise(status.content_id) &&
            status.status !== this.STATUSES.notStarted,
        );
        return statuses.length;
      },
      exportCSV() {
        const columns = [
          ...csvFields.name(),
          ...csvFields.avgScore(true),
          {
            name: this.coachString('exercisesCompletedLabel'),
            key: 'exercises',
          },
          {
            name: this.coachString('resourcesViewedLabel'),
            key: 'resources',
          },
          ...csvFields.lastActivity(),
        ];

        const exporter = new CSVExporter(columns, this.className);
        exporter.addNames({
          group: this.group.name,
        });

        exporter.export(this.table);
      },
    },
  };

</script>


<style lang="scss" scoped>

  @import '../common/print-table';

</style>
