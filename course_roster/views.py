from django.db import transaction
from django.http import HttpResponse
from django.template import Context, loader
from django.views.decorators.csrf import csrf_exempt
from django.core.context_processors import csrf
from blti import BLTI, BLTIException
from blti.views.rest_dispatch import RESTDispatch
from sis_provisioner.policy import UserPolicy, UserPolicyException
#from restclients.canvas.sections import Sections
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

        params['course_name'] = blti_data.get('context_title', 'this course')
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
            #sections = Sections().get_sections_in_course(course_id)
            enrollments = Enrollments().get_enrollments_for_course(
                course_id, {'page': page, 'per_page': 100})
        except DataFailureException as err:
            return self.error_response(500, err)
        except Exception as err:
            return self.error_response(400, err)

        #section_lookup = {}
        #for section in sections:
        #    section_lookup[section.section_id] = section

        people = {}
        role_counts = {}
        policy = UserPolicy()
        for enrollment in enrollments:
            #section_name = section_lookup[enrollment.section_id].name

            if enrollment.role in role_counts:
                role_counts[enrollment.role] += 1
            else:
                role_counts[enrollment.role] = 1

            if enrollment.user_id in people:
                #people[enrollment.user_id]['sections'].append(section_name)
                people[enrollment.user_id]['roles'].append(enrollment.role)
                continue

            try:
                policy.valid_reg_id(enrollment.sis_user_id)
                photo_url = IDPhoto(reg_id=enrollment.sis_user_id).get_url()

            except UserPolicyException:
                photo_url = IDPhoto().get_nophoto_url()

            people[enrollment.user_id] = {
                'user_url': enrollment.html_url,
                'photo_url': photo_url,
                #'sections': [section_name],
                'roles': [enrollment.role],
                'login_id': enrollment.login_id,
                'name': enrollment.name,
                'sortable_name': enrollment.sortable_name,
            }

        roles = []
        for role in sorted(role_counts.iterkeys()):
            roles.append({
                'role': role,
                'count': role_counts.get(role, 0)
            })

        data = {
            'people': sorted(people.values(),
                             key=lambda p: p['sortable_name']),
            'roles': roles,
        }

        return self.json_response(data)
