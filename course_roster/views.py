from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, StreamingHttpResponse
from django.template import Context, loader
from django.views.decorators.csrf import csrf_exempt
from django.core.context_processors import csrf
from blti import BLTI, BLTIException
from blti.views.rest_dispatch import RESTDispatch
from sis_provisioner.policy import UserPolicy, UserPolicyException
from restclients.canvas.users import Users
from restclients.canvas.sections import Sections
from restclients.exceptions import DataFailureException
from course_roster.models import IDPhoto
from urlparse import urlparse, urlunparse, parse_qs
from urllib import urlencode
import logging


logger = logging.getLogger(__name__)
NOPHOTO_URL = getattr(settings, 'COURSE_ROSTER_NOPHOTO_URL',
    'https://www.gravatar.com/avatar/00000000000000000000000000000000?s=120&d=mm&f=y')


@csrf_exempt
def Main(request, template='course_roster/main.html'):
    params = {}
    status_code = 200
    try:
        blti = BLTI()
        blti_data = blti.validate(request, visibility=BLTI.ADMIN)
        canvas_login_id = blti_data.get('custom_canvas_user_login_id', None)
        canvas_sis_user_id = blti_data.get('lis_person_sourcedid', None)
        canvas_course_id = blti_data.get('custom_canvas_course_id', None)

        blti.set_session(request,
                         user_id=canvas_login_id,
                         sis_user_id=canvas_sis_user_id,
                         canvas_course_id=canvas_course_id)

        params['canvas_course_id'] = canvas_course_id
        params['course_name'] = blti_data.get('context_label', 'this course')
        params['nophoto_url'] = NOPHOTO_URL
        params['session_id'] = request.session.session_key
    except BLTIException as err:
        status_code = 401
        template = 'blti/401.html'
        params['validation_error'] = err
    except Exception as err:
        status_code = 500
        template = 'blti/error.html'
        params['validation_error'] = err

    t = loader.get_template(template)
    c = Context(params)
    c.update(csrf(request))
    return HttpResponse(t.render(c), status=status_code)


def RosterPhoto(request, photo_key):
    try:
        return StreamingHttpResponse(
            IDPhoto.objects.get(url_key=photo_key).get(),
            content_type='image/jpeg')
    except DataFailureException as err:
        return HttpResponse(status=err.status)
    except IDPhoto.DoesNotExist:
        return HttpResponse(status=404)


class CourseRoster(RESTDispatch):
    @transaction.atomic
    def GET(self, request, **kwargs):
        course_id = kwargs.get('canvas_course_id', None)
        page = request.GET.get('page', 1)

        if not course_id:
            return self.error_response(400, 'Missing course ID')

        search_params = {
            'page': page,
            'per_page': getattr(settings, 'COURSE_ROSTER_PER_PAGE', 30),
            'include': ['enrollments', 'avatar_url'],
        }

        canvas = Users()
        try:
            users = canvas.get_users_for_course(course_id, search_params)
        except DataFailureException as err:
            return self.error_response(500, err.msg)

        people = []
        policy = UserPolicy()
        for user in users:
            try:
                policy.valid_reg_id(user.sis_user_id)
                photo_url = IDPhoto(reg_id=user.sis_user_id).get_url()
                avatar_url = self._avatar_url(user.avatar_url)
            except UserPolicyException:
                try:
                    policy.valid_gmail_id(user.login_id)
                    photo_url = self._avatar_url(user.avatar_url)
                    avatar_url = NOPHOTO_URL
                except UserPolicyException:
                    continue

            search_name = '%s %s' % (user.name, user.login_id)
            people.append({
                'user_url': user.enrollments[0].html_url,
                'photo_url': photo_url,
                'avatar_url': avatar_url,
                'login_id': user.login_id,
                'name': user.name,
                'search_name': search_name.lower(),
                'sections': [e.section_id for e in user.enrollments],
            })

        if len(people):
            try:
                url_parts = urlparse(canvas.next_page_url)
                next_page = parse_qs(url_parts.query).get('page', [])[0]
            except Exception as err:
                next_page = None

            return self.json_response({
                'people': people,
                'next_page': next_page
            })
        else:
            return self.error_response(404)

    def _avatar_url(self, url):
        url_parts = urlparse(url)
        if 'gravatar.com' in url_parts.netloc:
            new_parts = url_parts._replace(
                query=urlencode({'s': 120, 'd': 'mm'})
            )
            return urlunparse(new_parts)
        return url


class CourseSections(RESTDispatch):
    """ Performs actions on Canvas Course Sections
        GET returns 200 with course sections.
    """
    def GET(self, request, **kwargs):
        course_id = kwargs['canvas_course_id']
        sections = []

        try:
            for section in Sections().get_sections_in_course(course_id):
                sections.append({
                    'id': section.section_id,
                    'sis_id': section.sis_section_id,
                    'name': section.name
                })
        except DataFailureException as err:
            return self.error_response(500, err.msg)

        return self.json_response({'sections': sorted(
            sections, key=lambda k: k['name'])})
