from marshmallow import Schema, fields
from api.serializers.user import UserSummarySchema
from api.serializers.image import MediaSchema, CreateMediaSchema


class BrandCategorySchema(Schema):
    id = fields.String(required=True, dump_only=True)
    name = fields.String(required=True)
    number_of_brands = fields.Function(lambda obj: len(obj.brands))


class BrandSummarySchema(Schema):
    id = fields.String(required=True, dump_only=True)
    name = fields.String(required=True)
    image = fields.Nested(MediaSchema, required=True)
    endorsement_count = fields.Function(lambda obj: len(obj.endorsements))


class BrandValidationSchema(Schema):
    id = fields.String(required=True)
    validator = fields.Nested(UserSummarySchema, required=True)
    created_at = fields.DateTime(required=True)
    brand = fields.Nested(BrandSummarySchema, required=True)


class BrandSchema(Schema):
    id = fields.String(required=True, dump_only=True)
    name = fields.String(required=True)
    description = fields.String(required=True)
    image = fields.Nested(MediaSchema, required=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    creator = fields.Nested(UserSummarySchema)
    country = fields.String(required=True)
    category = fields.Nested(BrandCategorySchema)
    endorsement_count = fields.Function(lambda obj: len(obj.endorsements))
    endorsements = fields.Nested(BrandValidationSchema, many=True, )
    founder = fields.Function(lambda obj:  obj.founder.split(",") if obj.founder else None)
    founded_date = fields.Date(required=True)


class CreateBrandSchema(Schema):
    name = fields.String(required=True)
    description = fields.String(required=True)
    category_id = fields.String(required=True)
    image = fields.Nested(CreateMediaSchema, required=True)
    creator = fields.Nested(UserSummarySchema)
    country = fields.String(required=True)
    founder = fields.List(fields.String(), required=True)
    founded_date = fields.String(required=True)

