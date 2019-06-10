from api.views import *
from api.serializers.job import JobSchema
from api.views.auth_base import AuthBaseView
from api.models.event import Job


job_schema = JobSchema()


class JobView(AuthBaseView):

    def index(self):
        jobs = Job.get_jobs()
        return response({
            'jobs': job_schema.dump(jobs, many=True)
        })

    @route('/search', methods=['GET'])
    def search(self):
        if 'q' in request.args:
            searchterm = request.args['q']
            jobs = Job.find_job_by_searchterm(searchterm)
            return response({
                'ok': True,
                'jobs': job_schema.dump(jobs, many=True)
            })
        else:
            return response({
                'ok': False,
                'message': 'Bad request',
                'errors': {
                    'q': 'search parameter q is missing'
                }
            })


