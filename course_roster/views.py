from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.template import Context, loader
from django.views.decorators.csrf import csrf_exempt
from django.core.context_processors import csrf
from blti import BLTI, BLTIException
from blti.views.rest_dispatch import RESTDispatch
from sis_provisioner.policy import UserPolicy, UserPolicyException
from restclients.canvas.enrollments import Enrollments
from restclients.exceptions import DataFailureException
from course_roster.models import IDPhoto
import logging


logger = logging.getLogger(__name__)


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

        params['course_name'] = blti_data.get('context_label', 'this course')
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
        return HttpResponse(IDPhoto.objects.get(url_key=photo_key).get(),
                            content_type='image/jpeg')
    except DataFailureException as err:
        return HttpResponse(status=err.status)
    except IDPhoto.DoesNotExist:
        return HttpResponse(status=404)


class CourseRoster(RESTDispatch):
    @transaction.atomic
    def GET(self, request, **kwargs):
        page = kwargs.get('page', 1)
        try:
            blti = BLTI().get_session(request)
            course_id = blti.get('canvas_course_id', None)
            search_params = {
                'page': page,
                'per_page': getattr(settings, 'COURSE_ROSTER_PER_PAGE', 30),
            }
            enrollments = Enrollments().get_enrollments_for_course(
                course_id, search_params)
        except DataFailureException as err:
            return self.error_response(500, err)
        except Exception as err:
            return self.error_response(400, err)

        people = []
        seen_people = {}
        policy = UserPolicy()
        for enrollment in enrollments:
            if enrollment.user_id in seen_people:
                continue

            try:
                policy.valid_reg_id(enrollment.sis_user_id)
                photo_url = IDPhoto(reg_id=enrollment.sis_user_id).get_url()

            except UserPolicyException:
                photo_url = IDPhoto().get_nophoto_url()

            people.append({
                'user_url': enrollment.html_url,
                'photo_url': photo_url,
                'login_id': enrollment.login_id,
                'name': enrollment.name,
            })
            seen_people[enrollment.user_id] = None

        return self.json_response({'people': people})
