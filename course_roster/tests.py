# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.test import TestCase
from course_roster.dao.canvas import *
from course_roster.dao.idcard import *
import mock
import re


class CanvasDAOTest(TestCase):
    @mock.patch('course_roster.dao.canvas.Users')
    def test_users_constructor(self, mock_object):
        r = get_users_for_course('123', '456', '10')
        mock_object.assert_called_with(as_user='456')

    @mock.patch.object(Users, 'next_page_url', create=True)
    @mock.patch.object(Users, 'get_users_for_course')
    def test_get_course_users(self, mock_method, mock_attribute):
        with self.settings(COURSE_ROSTER_PER_PAGE=1000):
            r = get_users_for_course('123', '456', '10')
            mock_method.assert_called_with('123', params={
                'page': '10',
                'per_page': 1000,
                'enrollment_state': ['active'],
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

    def test_get_viewable_sections(self):
        pass


class IDPhotoTest(TestCase):
    @mock.patch.object(PWS, 'get_idcard_photo')
    def test_get_idphoto(self, mock_method):
        reg_id = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
        image_size = 120

        url = get_photo_url(reg_id, image_size)

        result = re.search(r'/([a-z0-9]{16})$', url)
        url_key = result.group(1)

        r = get_photo(url_key)
        mock_method.assert_called_with(reg_id, size=image_size)

        # Key no longer exists
        self.assertRaises(ObjectDoesNotExist, get_photo, url_key)

    def test_get_photo_url(self):
        reg_id = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
        image_size = 120

        self.assertRegexpMatches(
            get_photo_url(reg_id, image_size), r'/[a-z0-9]{16}$')

    def test_get_photo_url_with_invalid_reg_id(self):
        reg_id = 'invalid'
        image_size = 120

        self.assertEqual(get_photo_url(reg_id, image_size), None)

    def test_get_avatar_url(self):
        image_size = 120
        self.assertEqual(
            get_avatar_url('http://xyz.edu/img/123.png', image_size),
            'http://xyz.edu/img/123.png')
        self.assertEqual(
            get_avatar_url('https://gravatar.com/avatar/abcdef?s=320',
                           image_size),
            'https://gravatar.com/avatar/abcdef?s=120&d=mm')
