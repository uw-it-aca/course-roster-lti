from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, StreamingHttpResponse
from django.template import Context, loader
from django.views.decorators.csrf import csrf_exempt
from django.core.context_processors import csrf
from django.contrib.staticfiles.templatetags.staticfiles import static
from blti import BLTI, BLTIException
from blti.views.rest_dispatch import RESTDispatch
from sis_provisioner.policy import UserPolicy, UserPolicyException
from restclients.canvas.enrollments import Enrollments
from restclients.canvas.sections import Sections
from restclients.exceptions import DataFailureException
from course_roster.models import IDPhoto
import logging


logger = logging.getLogger(__name__)
NOPHOTO_URL = static('course_roster/img/nophoto.jpg')


@csrf_exempt
def Main(request, template='course_roster/main.html'):
    params = {}
    status_code = 200
    try:
        blti = BLTI()
        blti_data = blti.validate(request)
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
    except Exception as err:
        template = 'blti/error.html'
        params['validation_error'] = err
        status_code = 401

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
        course_id = kwargs.get('canvas_course_id')
        section_id = request.GET.get('canvas_section_id', None)
        search_term = request.GET.get('search_term', None)
        page = request.GET.get('page', 1)

        search_params = {
            'page': page,
            'per_page': getattr(settings, 'COURSE_ROSTER_PER_PAGE', 30),
        }

        canvas = Enrollments()
        try:
            if section_id is not None and len(section_id):
                enrollments = canvas.get_enrollments_for_section(
                    section_id, search_params)

            elif course_id is not None and len(course_id):
                if search_term is not None and len(search_term):
                    enrollments = canvas.search_enrollments_for_course(
                        course_id, search_term, search_params)
                else:
                    enrollments = canvas.get_enrollments_for_course(
                        course_id, search_params)

            else:
                return self.error_response(400, 'Missing course or section ID')

        except DataFailureException as err:
            return self.error_response(500, err.msg)

        people = []
        seen_people = {}
        policy = UserPolicy()
        for enrollment in enrollments:
            if enrollment.user_id in seen_people:
                continue
            seen_people[enrollment.user_id] = None

            try:
                policy.valid_reg_id(enrollment.sis_user_id)
                photo_url = IDPhoto(reg_id=enrollment.sis_user_id).get_url()
            except UserPolicyException:
                try:
                    policy.valid_gmail_id(enrollment.login_id)
                    photo_url = NOPHOTO_URL
                except UserPolicyException:
                    continue

            people.append({
                'user_url': enrollment.html_url,
                'photo_url': photo_url,
                'login_id': enrollment.login_id,
                'name': enrollment.name,
            })

        if len(people):
            return self.json_response({'people': people})
        else:
            return self.error_response(404)


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
