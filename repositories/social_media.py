from api.repositories.base import Repository
from api.models.event import SocialMedia


class SocialMediaRepository(Repository):

    def get_all(self):
        media = self.session.query(SocialMedia).all()
        return media