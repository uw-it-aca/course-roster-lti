from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, StreamingHttpResponse
from django.core.context_processors import csrf
from django.utils.timezone import utc
from django.views.generic import View
from blti.views import BLTILaunchView
from blti.views.rest_dispatch import RESTDispatch
from sis_provisioner.policy import UserPolicy, UserPolicyException
from restclients.canvas.enrollments import Enrollments
from restclients.canvas.users import Users
from restclients.canvas.sections import Sections
from restclients.exceptions import DataFailureException
from restclients.util.retry import retry
from urllib3.exceptions import SSLError
from course_roster.models import IDPhoto
from datetime import datetime, timedelta
from urlparse import urlparse, urlunparse, parse_qs
from urllib import urlencode
import logging


logger = logging.getLogger(__name__)


class LaunchView(BLTILaunchView):
    template_name = 'course_roster/main.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        request = kwargs.get('request')
        blti_data = kwargs.get('blti_params')

        context = {
            'session_id': request.session.session_key,
            'canvas_course_id': blti_data.get('custom_canvas_course_id'),
            'course_name': blti_data.get('context_label', 'this course')
        }
        context.update(csrf(request))
        return context


class RosterPhoto(View):
    cache_time = 60 * 60 * 4
    date_format = '%a, %d %b %Y %H:%M:%S GMT'

    def get(self, request, *args, **kwargs):
        photo_key = kwargs.get('photo_key')
        now = datetime.utcnow()
        expires = now + timedelta(seconds=self.cache_time)
        try:
            response = StreamingHttpResponse(
                IDPhoto.objects.get(url_key=photo_key).get(),
                content_type='image/jpeg')
            response['Cache-Control'] = 'public,max-age=%s' % self.cache_time
            response['Expires'] = expires.strftime(self.date_format)
            response['Last-Modified'] = now.strftime(self.date_format)
            return response
        except DataFailureException as err:
            return HttpResponse(status=err.status)
        except IDPhoto.DoesNotExist:
            status = 304 if ('HTTP_IF_MODIFIED_SINCE' in request.META) else 404
            return HttpResponse(status=status)


class CourseRoster(RESTDispatch):
    @transaction.atomic
    def GET(self, request, **kwargs):
        course_id = kwargs.get('canvas_course_id', None)
        image_size = request.GET.get('image_size', 120)
        page = request.GET.get('page', 1)

        if not course_id:
            return self.error_response(400, 'Missing course ID')

        blti_data = self.get_session(request)
        user_id = blti_data.get('custom_canvas_user_id')

        params = {
            'page': page,
            'per_page': getattr(settings, 'COURSE_ROSTER_PER_PAGE', 50),
            'enrollment_type': ['student'],
            'include': ['enrollments', 'avatar_url']
        }

        @retry(SSLError, tries=3, delay=1, logger=logger)
        def _get_users_for_course(canvas, course_id, params):
            return canvas.get_users_for_course(course_id, params)

        canvas = Users(as_user=user_id)
        try:
            users = _get_users_for_course(canvas, course_id, params)
        except DataFailureException as err:
            return self.error_response(500, err.msg)

        people = []
        policy = UserPolicy()
        for user in users:
            try:
                policy.valid_reg_id(user.sis_user_id)
                photo_url = IDPhoto(reg_id=user.sis_user_id,
                                    image_size=image_size).get_url()
                avatar_url = self._avatar_url(user.avatar_url, image_size)
            except UserPolicyException:
                try:
                    policy.valid_gmail_id(user.login_id)
                    photo_url = self._avatar_url(user.avatar_url, image_size)
                    avatar_url = ''
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

        try:
            url_parts = urlparse(canvas.next_page_url)
            next_page = parse_qs(url_parts.query).get('page', [])[0]
        except Exception as err:
            next_page = None

        return self.json_response({
            'people': people,
            'next_page': next_page
        })

    def _avatar_url(self, url, image_size):
        url_parts = urlparse(url)
        if 'gravatar.com' in url_parts.netloc:
            new_parts = url_parts._replace(
                query=urlencode({'s': image_size, 'd': 'mm'})
            )
            return urlunparse(new_parts)
        return url


class CourseSections(RESTDispatch):
    """ Performs actions on Canvas Course Sections
        GET returns 200 with course sections.
    """
    def GET(self, request, **kwargs):
        course_id = kwargs['canvas_course_id']
        blti_data = self.get_session(request)
        user_id = blti_data.get('custom_canvas_user_id')

        @retry(SSLError, tries=3, delay=1, logger=logger)
        def _get_enrollments_for_course(course_id, user_id):
            return Enrollments().get_enrollments_for_course(
                course_id, {'user_id': user_id})

        @retry(SSLError, tries=3, delay=1, logger=logger)
        def _get_sections_for_course(course_id, user_id):
            return Sections(as_user=user_id).get_sections_in_course(course_id)

        sections = []
        try:
            limit_privileges_to_course_section = False
            limit_sections = {}
            for enrollment in _get_enrollments_for_course(course_id, user_id):
                if enrollment.limit_privileges_to_course_section:
                    limit_privileges_to_course_section = True
                    limit_sections[enrollment.section_id] = True

            for section in _get_sections_for_course(course_id, user_id):
                if (limit_privileges_to_course_section and
                        section.section_id not in limit_sections):
                    continue

                sections.append({
                    'id': section.section_id,
                    'name': section.name
                })
        except DataFailureException as err:
            return self.error_response(500, err.msg)

        return self.json_response({'sections': sorted(
            sections, key=lambda k: k['name'])})
