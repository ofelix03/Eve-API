from marshmallow import ValidationError

from . import *
from api.serializers.user import CountrySerializer
from api.repositories import exceptions

country_serializer = CountrySerializer()
from api.serializers import image_schema
from api.libs.cloudinary import upload as cloudinary_upload
from api.libs.cloudinary import api as cloudinary_api


class MediaFile(object):
    def __init__(self, filename=None, format=None, source_url=None, public_id=None):
        self.filename = filename
        self.format = format
        self.source_url = source_url
        self.public_id = public_id

    def add_source_url(self, url):
        self.source_url = url

    def add_format(self, format):
        self.format = format

    def add_filename(self, filename):
        self.filename = filename

    def add_public_id(self, public_id):
        self.public_id = public_id


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
                    media_file.add_public_id(resp['public_id'])
                    uploaded_media.append(media_file)
                return response(image_schema.dump(uploaded_media, many=True))
        except Exception as e:
            return response({
                "ok": False,
                "code": "IMAGE_UPLOAD_FAILED",
                "message": e
            }, 400)

    @route('/<string:mediaId>')
    def delete_media(self, media_id):
        try:
            cloudinary_api.delete_resources(media_id)
            return response(None)
        except exceptions.EventNotFound:
            return response({
                'ok': False,
                'code': 'EVENT_NOT_FOUND'
            }, 400)
        except exceptions.MediaNotFound:
            return response({
                'ok': False,
                'code': 'MEDIA_NOT_FOUND'
            }, 400)
