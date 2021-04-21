# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from uw_canvas.users import Users
from uw_canvas.sections import Sections
from uw_canvas.enrollments import Enrollments


def get_users_for_course(course_id, user_id, page):
    canvas = Users(as_user=user_id)
    users = canvas.get_users_for_course(course_id, params={
        'page': page,
        'per_page': getattr(settings, 'COURSE_ROSTER_PER_PAGE', 50),
        'enrollment_type': ['student'],
        'enrollment_state': ['active'],
        'include': ['enrollments', 'avatar_url']})
    return (users, canvas.next_page_url)


def get_enrollments_for_course(course_id, user_id):
    return Enrollments().get_enrollments_for_course(course_id, params={
        'user_id': user_id})


def get_sections_in_course(course_id, user_id):
    return Sections(as_user=user_id).get_sections_in_course(course_id)


def get_viewable_sections(course_id, user_id):
    limit_privileges_to_course_section = False
    limit_sections = {}
    for enrollment in get_enrollments_for_course(course_id, user_id):
        if enrollment.limit_privileges_to_course_section:
            limit_privileges_to_course_section = True
            limit_sections[enrollment.section_id] = True

    sections = []
    for section in get_sections_in_course(course_id, user_id):
        if (limit_privileges_to_course_section and
                section.section_id not in limit_sections):
            continue

        sections.append({
            'id': section.section_id,
            'name': section.name
        })
    return sections
