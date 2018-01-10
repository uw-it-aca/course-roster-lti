from django.db import transaction
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.timezone import utc
from django.views.generic import View
from blti.views import BLTILaunchView, RESTDispatch
from sis_provisioner.dao.user import valid_reg_id, valid_gmail_id
from sis_provisioner.exceptions import UserPolicyException
from restclients_core.exceptions import DataFailureException
from course_roster.dao.canvas import (
    get_users_for_course, get_viewable_sections)
from course_roster.models import IDPhoto
from datetime import datetime, timedelta
try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs


class LaunchView(BLTILaunchView):
    template_name = 'course_roster/main.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        request = kwargs.get('request')

        return {
            'session_id': request.session.session_key,
            'canvas_course_id': self.blti.canvas_course_id,
            'course_name': self.blti.course_short_name,
        }


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
    authorized_role = 'admin'

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('canvas_course_id', None)
        image_size = request.GET.get('image_size', 120)
        page = request.GET.get('page', 1)
        user_id = self.blti.canvas_user_id

        if not course_id:
            return self.error_response(400, 'Missing course ID')

        try:
            (users, next_url) = get_users_for_course(course_id, user_id, page)
        except DataFailureException as err:
            return self.error_response(500, err.msg)

        people = []
        for user in users:
            idphoto = IDPhoto(image_size=image_size)
            try:
                valid_reg_id(user.sis_user_id)
                idphoto.reg_id = user.sis_user_id
                photo_url = idphoto.get_url()
                avatar_url = idphoto.get_avatar_url(user.avatar_url)
            except UserPolicyException:
                try:
                    valid_gmail_id(user.login_id)
                    photo_url = idphoto.get_avatar_url(user.avatar_url)
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
            url_parts = urlparse(next_url)
            next_page = parse_qs(url_parts.query).get('page', [])[0]
        except Exception as err:
            next_page = None

        return self.json_response({
            'people': people,
            'next_page': next_page
        })


class CourseSections(RESTDispatch):
    """ Performs actions on Canvas Course Sections
        GET returns 200 with course sections.
    """
    authorized_role = 'admin'

    def get(self, request, *args, **kwargs):
        course_id = kwargs['canvas_course_id']
        user_id = self.blti.canvas_user_id

        try:
            sections = get_viewable_sections(course_id, user_id)
        except DataFailureException as err:
            return self.error_response(500, err.msg)

        return self.json_response({'sections': sorted(
            sections, key=lambda k: k['name'])})
