from marshmallow import ValidationError

from . import *
from api.serializers.user import CountrySerializer
from api.models.event import Country
from api.repositories import exceptions

country_serializer = CountrySerializer()
from api.serializers import image_schema
from api.libs.cloudinary import upload as cloudinary_upload
from api.libs.cloudinary import api as cloudinary_api


class MediaFile(object):
    def __init__(self, filename=None, format=None, source_url=None):
        self.filename = filename
        self.format = format
        self.source_url = source_url

    def add_source_url(self, url):
        self.source_url = url

    def add_format(self, format):
        self.format = format

    def add_filename(self, filename):
        self.filename = filename


class ImagesView(FlaskView):

    @route('upload', methods=['POST'])
    def upload_media(self):
        try:
            print("Upload Images")
            if request.method == 'POST':
                uploaded_media = []
                for key in request.files:
                    file_to_upload = request.files[key]
                    media_file = MediaFile()
                    resp = cloudinary_upload(file_to_upload, public_id=media_file.filename if  media_file.filename else None)
                    media_file.add_format(resp['format'])
                    media_file.add_source_url(resp['url'])
                    uploaded_media.append(media_file)
                return response(image_schema.dump(uploaded_media, many=True))
        except Exception as e:
            print('exception##', e)
            return response({
                "ok": False,
                "code": "IMAGE_UPLOAD_FAILED",
                "message": e
            }, 400)
