"""
Implements a custom auth backend as described in the Django docs. Notably authentication could be provided by the
default Django backend, but authorization (i.e. permissions checking) must be handled by our custom backends since we
do not use the regular Django permissions. See handling authorization docs. Should then be listed in the
AUTHENTICATION_BACKENDS. Note that authentication backends are checked in the order they're listed.
"""
import functools

from kolibri.auth.models import BaseUser, DeviceOwner, FacilityUser, Classroom
from kolibri.core.errors import KolibriError


class BaseBackend(object):
    """
    Provides the authentication parts that are common to both backends.
    """
    def _authenticate(self, username=None, password=None):
        """
        Returns a BaseUser object if authentication succeeds, else None.

        :param username: A string
        :param password: A string
        """
        try:
            user = BaseUser.objects.get(username=username)
            if user.check_password(password):
                return user
            else:
                return None
        except BaseUser.DoesNotExist:
            return None


class FacilityBackend(BaseBackend):
    """
    A class that implements permissions checking for Facility Users. Always returns False if the user is a DeviceAdmin,
    in order to avoid unnecessary database queries.
    """

    def authenticate(self, username=None, password=None):
        """
        Authenticates the user if the credentials correspond to a Facility User

        :param username: a string
        :param password: a string
        :return: A FacilityUser instance if successful, or None if authentication failed *or* the authentication was
          successful but the user is a DeviceOwner.
        """
        user = self._authenticate(username, password)
        return FacilityUser.objects.get(pk=user.pk) if user and not user._is_device_owner else None

    def get_user(self, user_id):
        """
        Gets a user. Auth backends are required to implement this.

        :param user_id: A BaseUser pk
        :return: A FacilityUser instance if a BaseUser with that pk is found, else None.
        """
        try:
            user = FacilityUser.objects.get(pk=user_id)
            return user if not user._is_device_owner else None
        except FacilityUser.DoesNotExist:
            return None

    def has_perm(self, user_obj, perm, obj=None):
        """
        Returns True if the user has the specified permission. This function will defer to any number of other
        functions based on the value of perm. Always False if user_obj is a DeviceOwner.

        :param user_obj: One of the user proxy model instances
        :param perm: a string, the name of the permission
        :param obj: For row-level permissions, the object in question
        :return: True or False.
        """
        try:
            return _permissions_checkers[perm](user_obj, obj)
        except KeyError:
            raise InvalidPermission("Permission '{}' does not have a permission checking function".format(perm))

    def has_module_perms(self, user_obj, package_name):
        """
        Returns True if the user has any permissions in the given package (the Django app label).
        Always False if user_obj is a DeviceOwner.

        :param user_obj: One of the user proxy model instances
        :param package_name: A string, a django app label
        :return: True or False
        """
        raise NotImplementedError()

    def get_all_permissions(self, user_obj, obj=None):
        """
        Returns a list of all permissions strings the user has. If obj is specified, then returns all row-level
        permissions the user has related to that object.
        Always empty if user_obj is a DeviceOwner.

        :param user_obj: One of the user proxy model instances
        :param obj: For row-level permissions, the object in question
        :return: A list of permission strings. Could be empty if no permissions are found.
        """
        raise NotImplementedError()


class DeviceBackend(BaseBackend):
    """
    A very simple backend that, when passed in a user for permissions checking, returns True if the user is a
    DeviceAdmin, or False otherwise.
    """

    def authenticate(self, username=None, password=None):
        """
        Authenticates the user if the credentials correspond to a Device Owner.

        :param username: a string
        :param password: a string
        :return: A DeviceOwner instance if successful, or None if authentication failed *or* the authentication was
          successful but the user is a FacilityUser.
        """
        user = self._authenticate(username, password)
        return DeviceOwner.objects.get(pk=user.pk) if user and user._is_device_owner else None

    def get_user(self, user_id):
        """
        Gets a user. Auth backends are required to implement this.

        :param user_id: A BaseUser pk
        :return: A DeviceOwner instance if a BaseUser with that pk is found, else None.
        """
        try:
            user = DeviceOwner.objects.get(pk=user_id)
            return user if user._is_device_owner else None
        except DeviceOwner.DoesNotExist:
            return None

    def _has_perm(self, user_obj):
        return user_obj.is_device_owner()

    def has_perm(self, user_obj, perm, obj=None):
        return self._has_perm(user_obj)

    def has_module_perms(self, user_obj, package_name):
        return self._has_perm(user_obj)

    def get_all_permissions(self, user_obj, obj=None):
        """
        Returns a list of all permissions strings the user has. If obj is specified, then returns all row-level
        permissions the user has related to that object.
        Always empty if user_obj is a FacilityUser.

        :param user_obj: One of the user proxy model instances.
        :param obj: For row-level permissions, the object in question.
        :return: A list of permission strings. Empty if the user is a FacilityUser.
        """
        raise NotImplementedError()


class InvalidPermission(KolibriError):
    pass


def _reject_obj(perm, obj):
    if obj is not None:
        raise InvalidPermission("'{perm}' does not take an optional object. Got: {obj}".format(
            perm=perm, obj=repr(obj)))


def _deny(perm, user, obj=None):
    _reject_obj(perm, obj)
    return False


def _admin_only(user, obj):
    _reject_obj('auth.change_facility', obj)
    return user.is_facility_admin()


def _auth_add_classroom(user, obj):
    _reject_obj('auth.add_classroom', obj)
    return user.is_facility_admin()


def _assert_type(obj, _type):
    if isinstance(obj, _type):
        return True
    else:
        raise InvalidPermission('Expected object of type {}, but got {}'.format(repr(_type), repr(type(obj))))


def _coach_for_the_class(user, obj):
    """
    Permission formula for auth.change_classroom and auth.remove_classroom

    :param user: A FacilityUser object
    :param obj: The optional permissions object. Raises an InvalidPermission error if obj is not a Classroom.
    :return: True if the user is a Coach for the Classroom obj & True if the user is a FacilityAdmin, otherwise False
    """
    if obj is not None and _assert_type(obj, Classroom):
        return user.is_facility_admin() or (user in [role.user for role in obj.coaches()])
    else:
        return user.is_facility_admin()


_permissions_checkers = {
    'auth.add_facility': functools.partial(_deny, 'auth.add_facility'),
    'auth.remove_facility': functools.partial(_deny, 'auth.remove_facility'),
    'auth.change_facility': _admin_only,
    'auth.add_classroom': _auth_add_classroom,
    'auth.change_classroom': _coach_for_the_class,
    'auth.remove_classroom': _coach_for_the_class,
}
