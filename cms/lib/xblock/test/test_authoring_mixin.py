"""
Tests for the Studio authoring XBlock mixin.
"""


from django.conf import settings
from django.test.utils import override_settings
from xblock.core import XBlock

from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.lib.xmodule.xmodule.tests.test_export import PureXBlock
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.partitions.partitions import (  # lint-amnesty, pylint: disable=wrong-import-order
    ENROLLMENT_TRACK_PARTITION_ID,
    MINIMUM_STATIC_PARTITION_ID,
    Group,
    UserPartition
)


class AuthoringMixinTestCase(ModuleStoreTestCase):
    """
    Tests the studio authoring XBlock mixin.
    """
    GROUP_NO_LONGER_EXISTS = "This group no longer exists"
    NO_CONTENT_OR_ENROLLMENT_GROUPS = "Access to this component is not restricted"
    NO_CONTENT_ENROLLMENT_TRACK_ENABLED = "You can restrict access to this component to learners in specific enrollment tracks or content groups"  # lint-amnesty, pylint: disable=line-too-long
    NO_CONTENT_ENROLLMENT_TRACK_DISABLED = "You can restrict access to this component to learners in specific content groups"  # lint-amnesty, pylint: disable=line-too-long
    CONTENT_GROUPS_TITLE = "Content Groups"
    ENROLLMENT_GROUPS_TITLE = "Enrollment Track Groups"
    STAFF_LOCKED = 'The unit that contains this component is hidden from learners'

    FEATURES_WITH_ENROLLMENT_TRACK_DISABLED = settings.FEATURES.copy()
    FEATURES_WITH_ENROLLMENT_TRACK_DISABLED['ENABLE_ENROLLMENT_TRACK_USER_PARTITION'] = False

    @XBlock.register_temp_plugin(PureXBlock, 'pure')
    def setUp(self):
        """
        Create a simple course with a video component.
        """
        super().setUp()
        self.course = CourseFactory.create()
        chapter = ItemFactory.create(
            category='chapter',
            parent_location=self.course.location,
            display_name='Test Chapter'
        )
        sequential = ItemFactory.create(
            category='sequential',
            parent_location=chapter.location,
            display_name='Test Sequential'
        )
        vertical = ItemFactory.create(
            category='vertical',
            parent_location=sequential.location,
            display_name='Test Vertical'
        )
        video = ItemFactory.create(
            category='video',
            parent_location=vertical.location,
            display_name='Test Vertical'
        )
        pure = ItemFactory.create(
            category='pure',
            parent_location=vertical.location,
            display_name='Test Pure'
        )
        self.vertical_location = vertical.location
        self.video_location = video.location
        self.pure_location = pure.location
        self.pet_groups = [Group(1, 'Cat Lovers'), Group(2, 'Dog Lovers')]

    def create_content_groups(self, content_groups):
        """
        Create a cohorted user partition with the specified content groups.
        """
        # pylint: disable=attribute-defined-outside-init
        self.content_partition = UserPartition(
            MINIMUM_STATIC_PARTITION_ID,
            self.CONTENT_GROUPS_TITLE,
            'Contains Groups for Cohorted Courseware',
            content_groups,
            scheme_id='cohort'
        )
        self.course.user_partitions = [self.content_partition]
        self.store.update_item(self.course, self.user.id)

    def set_staff_only(self, item_location):
        """Make an item visible to staff only."""
        item = self.store.get_item(item_location)
        item.visible_to_staff_only = True
        self.store.update_item(item, self.user.id)

    def set_group_access(self, item_location, group_ids, partition_id=None):
        """
        Set group_access for the specified item to the specified group
        ids within the content partition.
        """
        item = self.store.get_item(item_location)
        item.group_access[self.content_partition.id if partition_id is None else partition_id] = group_ids
        self.store.update_item(item, self.user.id)

    def verify_visibility_view_contains(self, item_location, substrings):
        """
        Verify that an item's visibility view returns an html string
        containing all the expected substrings.
        """
        item = self.store.get_item(item_location)
        html = item.visibility_view().body_html()
        for string in substrings:
            self.assertIn(string, html)

    def verify_visibility_view_does_not_contain(self, item_location, substrings):
        """
        Verify that an item's visibility view returns an html string
        that does NOT contain the provided substrings.
        """
        item = self.store.get_item(item_location)
        html = item.visibility_view().body_html()
        for string in substrings:
            self.assertNotIn(string, html)

    def test_html_no_partition(self):
        self.verify_visibility_view_contains(self.video_location, [self.NO_CONTENT_OR_ENROLLMENT_GROUPS])

    def test_html_empty_partition(self):
        self.create_content_groups([])
        self.verify_visibility_view_contains(self.video_location, [self.NO_CONTENT_OR_ENROLLMENT_GROUPS])

    def test_html_populated_partition(self):
        self.create_content_groups(self.pet_groups)
        self.verify_visibility_view_contains(
            self.video_location,
            [self.CONTENT_GROUPS_TITLE, 'Cat Lovers', 'Dog Lovers']
        )

        self.verify_visibility_view_does_not_contain(
            self.video_location,
            [self.NO_CONTENT_OR_ENROLLMENT_GROUPS, self.ENROLLMENT_GROUPS_TITLE]
        )

    def test_html_no_partition_staff_locked(self):
        self.set_staff_only(self.vertical_location)
        self.verify_visibility_view_contains(self.video_location, [self.NO_CONTENT_OR_ENROLLMENT_GROUPS])
        self.verify_visibility_view_does_not_contain(
            self.video_location,
            [self.STAFF_LOCKED, self.CONTENT_GROUPS_TITLE, self.ENROLLMENT_GROUPS_TITLE]
        )

    def test_html_empty_partition_staff_locked(self):
        self.create_content_groups([])
        self.set_staff_only(self.vertical_location)
        self.verify_visibility_view_contains(self.video_location, [self.NO_CONTENT_OR_ENROLLMENT_GROUPS])
        self.verify_visibility_view_does_not_contain(
            self.video_location,
            [self.STAFF_LOCKED, self.CONTENT_GROUPS_TITLE, self.ENROLLMENT_GROUPS_TITLE]
        )

    def test_html_populated_partition_staff_locked(self):
        self.create_content_groups(self.pet_groups)
        self.set_staff_only(self.vertical_location)
        self.verify_visibility_view_contains(
            self.video_location,
            [self.STAFF_LOCKED, self.CONTENT_GROUPS_TITLE, 'Cat Lovers', 'Dog Lovers']
        )

    def test_html_false_content_group(self):
        self.create_content_groups(self.pet_groups)
        self.set_group_access(self.video_location, ['false_group_id'])
        self.verify_visibility_view_contains(
            self.video_location,
            [self.CONTENT_GROUPS_TITLE, 'Cat Lovers', 'Dog Lovers', self.GROUP_NO_LONGER_EXISTS]
        )
        self.verify_visibility_view_does_not_contain(
            self.video_location,
            [self.STAFF_LOCKED]
        )

    def test_html_false_content_group_staff_locked(self):
        self.create_content_groups(self.pet_groups)
        self.set_staff_only(self.vertical_location)
        self.set_group_access(self.video_location, ['false_group_id'])
        self.verify_visibility_view_contains(
            self.video_location,
            [
                'Cat Lovers',
                'Dog Lovers',
                self.STAFF_LOCKED,
                self.GROUP_NO_LONGER_EXISTS
            ]
        )

    @override_settings(FEATURES=FEATURES_WITH_ENROLLMENT_TRACK_DISABLED)
    def test_enrollment_tracks_disabled(self):
        """
        Test that the "no groups" messages doesn't reference enrollment tracks if
        they are disabled.
        """
        self.verify_visibility_view_contains(
            self.video_location,
            [self.NO_CONTENT_OR_ENROLLMENT_GROUPS, self.NO_CONTENT_ENROLLMENT_TRACK_DISABLED]
        )
        self.verify_visibility_view_does_not_contain(self.video_location, [self.NO_CONTENT_ENROLLMENT_TRACK_ENABLED])

    def test_enrollment_track_partitions_only(self):
        """
        Test what is displayed with no content groups but 2 enrollment modes registered.
        In all the cases where no enrollment modes are explicitly added, only the default
        enrollment mode exists, and we do not show it as an option (unless the course staff
        member has previously selected it).
        """
        CourseModeFactory.create(course_id=self.course.id, mode_slug='audit')
        CourseModeFactory.create(course_id=self.course.id, mode_slug='verified')
        self.verify_visibility_view_contains(
            self.video_location,
            [self.ENROLLMENT_GROUPS_TITLE, 'audit course', 'verified course']
        )
        self.verify_visibility_view_does_not_contain(
            self.video_location,
            [self.NO_CONTENT_OR_ENROLLMENT_GROUPS, self.CONTENT_GROUPS_TITLE]
        )

    def test_enrollment_track_partitions_and_content_groups(self):
        """
        Test what is displayed with both enrollment groups and content groups.
        """
        CourseModeFactory.create(course_id=self.course.id, mode_slug='audit')
        CourseModeFactory.create(course_id=self.course.id, mode_slug='verified')
        self.create_content_groups(self.pet_groups)
        self.verify_visibility_view_contains(
            self.video_location,
            [
                self.CONTENT_GROUPS_TITLE, 'Cat Lovers', 'Dog Lovers',
                self.ENROLLMENT_GROUPS_TITLE, 'audit course', 'verified course'
            ]
        )
        self.verify_visibility_view_does_not_contain(
            self.video_location,
            [self.NO_CONTENT_OR_ENROLLMENT_GROUPS]
        )

    def test_missing_enrollment_mode(self):
        """
        Test that an enrollment mode that is no longer registered is displayed as 'deleted',
        regardless of the number of current enrollment modes in the course.
        """
        # Only 1 mode (the default) exists, so nothing initially shows in the visibility view.
        self.verify_visibility_view_contains(
            self.video_location,
            [self.NO_CONTENT_OR_ENROLLMENT_GROUPS, self.NO_CONTENT_ENROLLMENT_TRACK_ENABLED]
        )
        self.verify_visibility_view_does_not_contain(
            self.video_location, [self.ENROLLMENT_GROUPS_TITLE, self.GROUP_NO_LONGER_EXISTS]
        )

        # Set group_access to reference a missing mode.
        self.set_group_access(self.video_location, ['10'], ENROLLMENT_TRACK_PARTITION_ID)
        self.verify_visibility_view_contains(
            self.video_location, [self.ENROLLMENT_GROUPS_TITLE, self.GROUP_NO_LONGER_EXISTS]
        )

        # Add 2 explicit enrollment modes.
        CourseModeFactory.create(course_id=self.course.id, mode_slug='audit')
        CourseModeFactory.create(course_id=self.course.id, mode_slug='verified')
        self.verify_visibility_view_contains(
            self.video_location,
            [self.ENROLLMENT_GROUPS_TITLE, 'audit course', 'verified course', self.GROUP_NO_LONGER_EXISTS]
        )

    def test_pure_xblock_visibility(self):
        self.create_content_groups(self.pet_groups)
        self.verify_visibility_view_contains(
            self.pure_location,
            [self.CONTENT_GROUPS_TITLE, 'Cat Lovers', 'Dog Lovers']
        )

        self.verify_visibility_view_does_not_contain(
            self.pure_location,
            [self.NO_CONTENT_OR_ENROLLMENT_GROUPS, self.ENROLLMENT_GROUPS_TITLE]
        )
