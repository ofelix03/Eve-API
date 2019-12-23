from marshmallow import Schema, fields


class MediaSchema(Schema):
    filename = fields.String(required=True)
    format = fields.String(required=True)
    source_url = fields.String(required=True)