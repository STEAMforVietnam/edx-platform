"""
Dates Tab Views
"""


from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edx_django_utils import monitoring as monitoring_utils
from opaque_keys.edx.keys import CourseKey


from student.models import CourseEnrollment
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.context_processor import user_timezone_locale_prefs
from lms.djangoapps.courseware.courses import get_course_date_blocks, get_course_with_access
from lms.djangoapps.courseware.date_summary import TodaysDate, verified_upgrade_deadline_link
from lms.djangoapps.course_home_api.dates.v1.serializers import DatesTabSerializer
from openedx.core.djangoapps.enrollments.api import get_enrollment
# from openedx.features.course_experience.utils import dates_banner_should_display

from lms.djangoapps.grades.api import CourseGradeFactory


class DatesTabView(RetrieveAPIView):
    """
    **Use Cases**

        Request details for the Dates Tab

    **Example Requests**

        GET api/course_home/v1/dates/{course_key}

    **Response Values**

        Body consists of the following fields:

        course_date_blocks: List of serialized DateSummary objects. Each serialization has the following fields:
            complete: (bool) Meant to only be used by assignments. Indicates completeness for an
                assignment.
            date: (datetime) The date time corresponding for the event
            date_type: (str) The type of date (ex. course-start-date, assignment-due-date, etc.)
            description: (str) The description for the date event
            learner_has_access: (bool) Indicates if the learner has access to the date event
            link: (str) An absolute link to content related to the date event
                (ex. verified link or link to assignment)
            title: (str) The title of the date event
        learner_is_full_access: (bool) Indicates if the user is verified in the course
        user_timezone: (str) The user's preferred timezone
        verified_upgrade_link: (str) The link for upgrading to the Verified track in a course

    **Returns**

        * 200 on success with above fields.
        * 403 if the user is not authenticated.
        * 404 if the course is not available or cannot be seen.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = DatesTabSerializer

    def get(self, request, course_key_string):
        # Enable NR tracing for this view based on course
        monitoring_utils.set_custom_metric('course_id', course_key_string)
        monitoring_utils.set_custom_metric('user_id', request.user.id)
        monitoring_utils.set_custom_metric('is_staff', request.user.is_staff)

        course_key = CourseKey.from_string(course_key_string)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=False)



        is_staff = bool(has_access(request.user, 'staff', course_key))

        if not CourseEnrollment.is_enrolled(request.user, course_key) and not is_staff:
            return Response('User not enrolled.', status=401)

        course_grade = CourseGradeFactory().read(request.user, course)


        blocks = get_course_date_blocks(course, request.user, request, include_access=True, include_past_dates=True)

        learner_is_full_access = False
        enrollment = get_enrollment(request.user.username, course_key_string)
        if enrollment:
            learner_is_full_access = enrollment.get('mode') == 'verified'

        # User locale settings
        user_timezone_locale = user_timezone_locale_prefs(request)
        user_timezone = user_timezone_locale['user_timezone']

        data = {
            'course_date_blocks': [block for block in blocks if not isinstance(block, TodaysDate)],
            'learner_is_full_access': learner_is_full_access,
            'user_timezone': user_timezone,
            'verified_upgrade_link': verified_upgrade_deadline_link(request.user, course=course),
            'section_scores': list(course_grade.chapter_grades.values()),
        }
        context = self.get_serializer_context()
        context['learner_is_full_access'] = learner_is_full_access
        context['staff_access'] = is_staff
        context['course_key'] = course_key
        serializer = self.get_serializer_class()(data, context=context)

        return Response(serializer.data)
