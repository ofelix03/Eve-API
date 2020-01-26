from . import *
from api.serializers.social_media import SocialMediaSchema
from api.models.event import SocialMedia

social_media_schema = SocialMediaSchema()


class SocialMediaView(FlaskView):

    def index(self):
        media = SocialMedia.get_all()
        return response({
            'ok': True,
            'social_media': social_media_schema.dump(media, many=True)
        })