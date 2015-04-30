from rest_framework import permissons

class IsCaptain(permissions.BasePermission):
    """
    Object-level permission to only allow the captain of the team
    """

    def has_object_permission(self, request, view, team):
        if request.user and request.user.is_authenticated():
            return team.is_captain(request.user)
        return False