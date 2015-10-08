from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from blti import BLTI, BLTIException
from sis_provisioner.policy import UserPolicy, UserPolicyException
from sis_provisioner.views.rest_dispatch import RESTDispatch
from restclients.canvas.sections import Sections
from restclients.canvas.enrollments import Enrollments
from restclients.exceptions import DataFailureException
from course_roster.models import CanvasAvatar, IDPhotoAvatar
import logging
import json


logger = logging.getLogger(__name__)


@csrf_exempt
def Main(request, template='course_roster/main.html'):
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

    except Exception as err:
        response = render_to_response('blti/error.html', {
            'validation_error': err
        }, RequestContext(request))
        response.status_code = 401
        return response

    params = {}
    return render_to_response(template, params, RequestContext(request))


def Avatar(request, user_id):
    user_policy = UserPolicy()
    try:
        blti = BLTI().get_session(request)
    except Exception as err:
        return HttpResponse(status=400)

    try:
        user_policy.valid_reg_id(user_id)
        avatar = IDPhotoAvatar(reg_id=user_id)
        return HttpResponse(avatar.get(), content_type='image/jpeg')
    except DataFailureException as err:
        return HttpResponse(status=err.status)
    except UserPolicyException as err:
        try:
            user_policy.valid_canvas_id(user_id)
            avatar, created = CanvasAvatar.objects.get_or_create(
                user_id=user_id)
            response = avatar.get()
            return HttpResponse(response.data, response.getheaders())

        except UserPolicyException as err:
            return HttpResponse(status=400)
        except Exception as err:
            print err
            return HttpResponse(status=500)


class CourseRoster(RESTDispatch):
    def GET(self, request, **kwargs):
        try:
            blti = BLTI().get_session(request)
            course_id = blti.get('canvas_course_id', None)
            sections = Sections().get_sections_in_course(course_id)
            enrollments = Enrollments().get_enrollments_for_course(course_id)
        except DataFailureException as err:
            return self.error_response(500, err)
        except Exception as err:
            return self.error_response(400, err)

        section_lookup = {}
        for section in sections:
            section_lookup[section.section_id] = section

        people = {}
        role_counts = {}
        for enrollment in enrollments:
            section_name = section_lookup[enrollment.section_id].name

            if enrollment.role in role_counts:
                role_counts[enrollment.role] += 1
            else:
                role_counts[enrollment.role] = 1

            if enrollment.user_id in people:
                people[enrollment.user_id]['sections'].append(section_name)
                people[enrollment.user_id]['roles'].append(enrollment.role)

            else:
                try:
                    UserPolicy().valid_reg_id(enrollment.sis_user_id)
                    avatar_url, is_static = IDPhotoAvatar(
                        reg_id=enrollment.sis_user_id).get_url()

                except UserPolicyException as err:
                    try:
                        avatar = CanvasAvatar.objects.get(
                            user_id=enrollment.user_id)
                        avatar_url, is_static = avatar.get_url()
                    except CanvasAvatar.DoesNotExist:
                        avatar_url, is_static = CanvasAvatar(
                            user_id=enrollment.user_id).get_url()

                people[enrollment.user_id] = {
                    'user_url': enrollment.html_url,
                    'avatar_url': avatar_url,
                    'is_avatar_static': is_static,
                    'sections': [section_name],
                    'roles': [enrollment.role],
                    'login_id': enrollment.login_id,
                    'sis_user_id': enrollment.sis_user_id,
                    'name': enrollment.name,
                    'total_activity_time': enrollment.total_activity_time,
                    'last_activity_at': enrollment.last_activity_at.isoformat() if (
                        enrollment.last_activity_at is not None) else None,
                }

        roles = []
        for role in sorted(role_counts.iterkeys()):
            roles.append({
                'role': role,
                'count': role_counts.get(role, 0)
            })

        data = {
            'people': people.values(),
            'roles': roles,
        }

        return self.json_response(json.dumps(data))
