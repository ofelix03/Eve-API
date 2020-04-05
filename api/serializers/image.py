from marshmallow import Schema, fields


class MediaSchema(Schema):
    filename = fields.String(allow_none=True)
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    public_id = fields.String(required=True)


class CreateMediaSchema(MediaSchema):
    pass