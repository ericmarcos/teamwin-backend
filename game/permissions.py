from rest_framework import permissions


SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


class TeamPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if (request.method in SAFE_METHODS or
            request.user and
            request.user.is_authenticated()):
            return True
        return False

    def has_object_permission(self, request, view, team):
        if request.method in SAFE_METHODS:
            return True
        elif request.user and request.user.is_authenticated():
            return team.is_captain(request.user)
        return False


class IsCaptain(permissions.BasePermission):
    """
    Object-level permission to only allow the captain of the team
    """

    def has_object_permission(self, request, view, team):
        if request.user and request.user.is_authenticated():
            return team.is_captain(request.user)
        return False


class PoolPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if (request.method in SAFE_METHODS or
            request.user and
            request.user.is_authenticated() and
            request.user.is_staff):
            return True
        return False

    def has_object_permission(self, request, view, team):
        if (request.method in SAFE_METHODS or
            request.user and
            request.user.is_authenticated() and
            request.user.is_staff):
            return True
        return False
