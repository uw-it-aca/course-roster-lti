from django.test import TestCase
from course_roster.dao.canvas import *
import mock


class CanvasDAOTest(TestCase):
    @mock.patch('course_roster.dao.canvas.Users')
    def test_users_constructor(self, mock_object):
        r = get_users_for_course('123', '456', '10')
        mock_object.assert_called_with(as_user='456')

    @mock.patch.object(Users, 'get_users_for_course')
    def test_get_course_users(self, mock_method):
        with self.settings(COURSE_ROSTER_PER_PAGE=1000):
            r = get_users_for_course('123', '456', '10')
            mock_method.assert_called_with('123', params={
                'page': '10',
                'per_page': 1000,
                'enrollment_type': ['student'],
                'include': ['enrollments', 'avatar_url']})

    @mock.patch.object(Enrollments, 'get_enrollments_for_course')
    def test_get_enrollments_for_course(self, mock_method):
        r = get_enrollments_for_course('123', '456')
        mock_method.assert_called_with('123', params={'user_id': '456'})

    @mock.patch('course_roster.dao.canvas.Sections')
    def test_sections_constructor(self, mock_object):
        r = get_sections_in_course('123', '456')
        mock_object.assert_called_with(as_user='456')

    @mock.patch.object(Sections, 'get_sections_in_course')
    def test_get_sections_in_course(self, mock_method):
        r = get_sections_in_course('123', '456')
        mock_method.assert_called_with('123')

    def test_resize_avatar(self):
        self.assertEquals(
            resize_avatar('http://xyz.edu/img/123.png', '120'),
            'http://xyz.edu/img/123.png')
        self.assertEquals(
            resize_avatar('https://gravatar.com/avatar/abcdefg?s=320', '120'),
            'https://gravatar.com/avatar/abcdefg?s=120&d=mm')
