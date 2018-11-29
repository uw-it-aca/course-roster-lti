from django.conf import settings
from uw_canvas.users import Users
from uw_canvas.sections import Sections
from uw_canvas.enrollments import Enrollments
from restclients_core.util.retry import retry
from urllib3.exceptions import SSLError
from logging import getLogger


logger = getLogger(__name__)


@retry(SSLError, tries=3, delay=1, logger=logger)
def get_users_for_course(course_id, user_id, page):
    canvas = Users(as_user=user_id)
    users = canvas.get_users_for_course(course_id, params={
        'page': page,
        'per_page': getattr(settings, 'COURSE_ROSTER_PER_PAGE', 50),
        'enrollment_type': ['student'],
        'enrollment_state': ['active'],
        'include': ['enrollments', 'avatar_url']})
    return (users, canvas.next_page_url)


@retry(SSLError, tries=3, delay=1, logger=logger)
def get_enrollments_for_course(course_id, user_id):
    return Enrollments().get_enrollments_for_course(course_id, params={
        'user_id': user_id})


@retry(SSLError, tries=3, delay=1, logger=logger)
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
