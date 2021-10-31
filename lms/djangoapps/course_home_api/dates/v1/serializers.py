# pylint: disable=abstract-method
"""
Dates Tab Serializers. Represents the relevant dates for a Course.
"""


from rest_framework import serializers
from rest_framework.reverse import reverse

from lms.djangoapps.courseware.date_summary import VerificationDeadlineDate
from lms.djangoapps.course_home_api.mixins import DatesBannerSerializerMixin


class GradedTotalSerializer(serializers.Serializer):
    earned = serializers.FloatField()
    possible = serializers.FloatField()


class SubsectionScoresSerializer(serializers.Serializer):
    """
    Serializer for subsections in section_scores
    """
    display_name = serializers.CharField()
    due = serializers.DateTimeField()
    format = serializers.CharField()
    graded = serializers.BooleanField()
    graded_total = GradedTotalSerializer()
    percent_graded = serializers.FloatField()
    problem_scores = serializers.SerializerMethodField()
    show_correctness = serializers.CharField()
    show_grades = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_url(self, subsection):
        relative_path = reverse('jump_to', args=[self.context['course_key'], subsection.location])
        request = self.context['request']
        return request.build_absolute_uri(relative_path)

    def get_problem_scores(self, subsection):
        """Problem scores for this subsection"""
        problem_scores = [
            {
                'earned': score.earned,
                'possible': score.possible,
            }
            for score in subsection.problem_scores.values()
        ]
        return problem_scores

    def get_show_grades(self, subsection):
        return subsection.show_grades(self.context['staff_access'])


class SectionScoresSerializer(serializers.Serializer):
    """
    Serializer for sections in section_scores
    """
    display_name = serializers.CharField()
    subsections = SubsectionScoresSerializer(source='sections', many=True)


class DateSummarySerializer(serializers.Serializer):
    """
    Serializer for Date Summary Objects.
    """
    block_key = serializers.CharField(default=None)
    section_name = serializers.CharField(default=None)
    assignment_type = serializers.CharField(default=None)
    complete = serializers.NullBooleanField()
    date = serializers.DateTimeField()
    date_type = serializers.CharField()
    description = serializers.CharField()
    learner_has_access = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    link_text = serializers.CharField()
    title = serializers.CharField()
    extra_info = serializers.CharField()

    def get_learner_has_access(self, block):
        learner_is_full_access = self.context.get('learner_is_full_access', False)
        block_is_verified = (getattr(block, 'contains_gated_content', False) or
                             isinstance(block, VerificationDeadlineDate))
        return (not block_is_verified) or learner_is_full_access

    def get_link(self, block):
        if block.link:
            request = self.context.get('request')
            return request.build_absolute_uri(block.link)
        return ''


class DatesTabSerializer(DatesBannerSerializerMixin, serializers.Serializer):
    """
    Serializer for the Dates Tab
    """
    course_date_blocks = DateSummarySerializer(many=True)
    has_ended = serializers.BooleanField()
    learner_is_full_access = serializers.BooleanField()
    user_timezone = serializers.CharField()
    section_scores = SectionScoresSerializer(many=True)
