# pylint: disable=abstract-method
"""
Dates Tab Serializers. Represents the relevant dates for a Course.
"""


from rest_framework import serializers
from rest_framework.reverse import reverse
from pytz import UTC
from datetime import datetime

from lms.djangoapps.courseware.date_summary import VerificationDeadlineDate
from lms.djangoapps.course_home_api.mixins import DatesBannerSerializerMixin


class CourseGradeSerializer(serializers.Serializer):
    """
    Serializer for course grade
    """
    letter_grade = serializers.CharField()
    percent = serializers.FloatField()
    is_passing = serializers.BooleanField(source='passed')


class GradingPolicySerializer(serializers.Serializer):
    """
    Serializer for grading policy
    """
    assignment_policies = serializers.SerializerMethodField()
    grade_range = serializers.DictField(source='GRADE_CUTOFFS')

    def get_assignment_policies(self, grading_policy):
        return [{
            'num_droppable': assignment_policy['drop_count'],
            'num_total': float(assignment_policy['min_count']),
            'short_label': assignment_policy.get('short_label', ''),
            'type': assignment_policy['type'],
            'weight': assignment_policy['weight'],
        } for assignment_policy in grading_policy['GRADER']]


class SubsectionScoresSerializer(serializers.Serializer):
    """
    Serializer for subsections in section_scores
    """
    assignment_type = serializers.CharField(source='format')
    block_key = serializers.SerializerMethodField()
    display_name = serializers.CharField()
    has_graded_assignment = serializers.BooleanField(source='graded')
    num_points_earned = serializers.FloatField(source='graded_total.earned')
    num_points_possible = serializers.FloatField(source='graded_total.possible')
    percent_graded = serializers.FloatField()
    problem_scores = serializers.SerializerMethodField()
    show_correctness = serializers.CharField()
    show_grades = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_block_key(self, subsection):
        return str(subsection.location)

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

    def get_url(self, subsection):
        """
        Returns the URL for the subsection while taking into account if the course team has
        marked the subsection's visibility as hide after due.
        """
        hide_url_date = subsection.end if subsection.self_paced else subsection.due
        if (not self.context['staff_access'] and subsection.hide_after_due and hide_url_date
                and datetime.now(UTC) > hide_url_date):
            return None

        relative_path = reverse('jump_to', args=[self.context['course_key'], subsection.location])
        request = self.context['request']
        return request.build_absolute_uri(relative_path)

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
    completion_summary = serializers.DictField()
    course_grade = CourseGradeSerializer()
    grading_policy = GradingPolicySerializer()
    section_scores = SectionScoresSerializer(many=True)
    user_has_passing_grade = serializers.BooleanField()
