from marshmallow import Schema, fields
from api.serializers.user import UserSummarySchema


class BrandCategorySchema(Schema):
    id = fields.String(required=True, dump_only=True)
    name = fields.String(required=True)
    number_of_brands = fields.Function(lambda obj: len(obj.brands))


class BrandSchema(Schema):
    id = fields.String(required=True, dump_only=True)
    name = fields.String(required=True)
    description = fields.String(required=True)
    image = fields.String()
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    creator = fields.Nested(UserSummarySchema)
    country = fields.String(required=True)
    category = fields.Nested(BrandCategorySchema)
    validators_count = fields.Function(lambda obj: len(obj.validations))


class BrandSummarySchema(Schema):
    id = fields.String(required=True, dump_only=True)
    name = fields.String(required=True)
    image = fields.String()
    validators_count = fields.Function(lambda obj: len(obj.validations))


class CreateBrandSchema(Schema):
    name = fields.String(required=True)
    description = fields.String(required=True)
    category_id = fields.String(required=True)
    image = fields.String()
    country = fields.String(required=True)


class BrandValidationSchema(Schema):
    id = fields.String(required=True)
    validator = fields.Nested(UserSummarySchema, required=True)
    created_at = fields.DateTime(required=True)
    brand = fields.Nested(BrandSummarySchema, required=True)
