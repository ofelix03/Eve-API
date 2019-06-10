# from api.repositories.base import Repository
#
# from api.models.event import Job
#
#
# class JobNotFound(Exception):
#     pass
#
#
# class JobRepository(Repository):
#
#     def get_jobs(self):
#         return self.session.query(Job).all()
#
#     def find_job_by_searchterm(self, searchterm=None):
#         if searchterm is None:
#             return []
#
#         searchterm = '%' + searchterm + '%'
#         jobs = self.session.query(Job).filter(Job.name.ilike(searchterm)).all()
#         return jobs
#
#     def add_job(self, job):
#         self.session.add(job)
#         self.session.commit()
#
#     def remove_job(self, job_id):
#         if self.has_job(job_id):
#             return self.session.query(Job).get(job_id)
#
#         raise JobNotFound()
#
#     def has_job(self, job_id):
#         count = self.session.query(Job).filter(Job.id==job_id).count()
#         return count
#
#     def get_job(self, job_id):
#         return self.session.query(Job).filter(Job.id==job_id).first()
