# pylint: disable=abstract-method
"""
Course Home Serializers.
"""

from rest_framework import serializers

from openedx.core.djangoapps.courseware_api.utils import serialize_upgrade_info
from openedx.features.course_experience import DISPLAY_COURSE_SOCK_FLAG


class ReadOnlySerializer(serializers.Serializer):
    """Serializers have an abstract create & update, but we often don't need them. So this silences the linter."""

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class VerifiedModeSerializer(ReadOnlySerializer):
    """
    Serializer Mixin for displaying verified mode upgrade information.

    Requires 'course_overview', 'enrollment', and 'request' from self.context.
    """
    can_show_upgrade_sock = serializers.SerializerMethodField()
    verified_mode = serializers.SerializerMethodField()

    def get_can_show_upgrade_sock(self, _):
        course_overview = self.context['course_overview']
        return DISPLAY_COURSE_SOCK_FLAG.is_enabled(course_overview.id)

    def get_verified_mode(self, _):
        """Return verified mode information, or None."""
        course_overview = self.context['course_overview']
        enrollment = self.context['enrollment']
        request = self.context['request']
        return serialize_upgrade_info(request.user, course_overview, enrollment)
