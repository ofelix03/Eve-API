from marshmallow import Schema, fields


class SocialMediaSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)