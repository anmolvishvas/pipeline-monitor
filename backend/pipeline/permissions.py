from rest_framework.permissions import BasePermission


class IsOperator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated


class IsViewer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated