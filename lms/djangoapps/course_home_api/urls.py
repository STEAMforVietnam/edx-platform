"""
Contains all the URLs for the Course Home
"""


from django.conf import settings
from django.urls import re_path

from lms.djangoapps.course_home_api.course_metadata.views import CourseHomeMetadataView
from lms.djangoapps.course_home_api.dates.v1 import views

urlpatterns = []

# URL for Course metadata content
urlpatterns += [
    re_path(
        fr'course_metadata/{settings.COURSE_KEY_PATTERN}',
        CourseHomeMetadataView.as_view(),
        name='course-metadata'
    ),
]

# Dates Tab URLs
urlpatterns += [
    re_path(
        r'v1/dates/{}'.format(settings.COURSE_KEY_PATTERN),
        views.DatesTabView.as_view(),
        name='course-home-dates-tab'
    ),
]
