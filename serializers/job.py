from marshmallow import Schema, fields

class JobSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)