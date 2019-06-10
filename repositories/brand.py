from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from datetime import datetime

from api.repositories.base import Repository

from api.models.event import Brand, BrandCategory, BrandValidation

from api.repositories import exceptions


class BrandCategoryRepository(Repository):

    def has_category(self, category_id):
        count = self.session.query(BrandCategory).filter(BrandCategory.id==category_id).count()
        return bool(count)

    def get_categories(self):
        return self.session.query(BrandCategory).all()

    def get_category(self, category_id):
        if not self.has_category(category_id):
            raise exceptions.BrandCategoryNotFound()
        return self.session.query(BrandCategory).filter(BrandCategory.id==category_id).first()

    def remove_category(self, category_id):
        if not self.has_category(category_id):
            raise exceptions.BrandCategoryNotFound()
        self.session.query(BrandCategory).filter(BrandCategory.id==category_id).delete()

    def add_category(self, category):
        self.session.add(category)
        self.session.commit()

    def add_categories(self, categories):
        self.session.add_all(categories)
        self.session.commit()

    def update_category(self, category_id, name):
        if not self.has_category(category_id):
            raise exceptions.BrandCategoryNotFound()

        category = self.get_category(category_id)
        category.name = name
        self.session.commit()


class BrandRepository(Repository):

    def has_brand(self, brand_id):
        count = self.session.query(Brand).filter(Brand.id==brand_id).count()
        return bool(count)

    def get_brands(self, category_id=None, searchterm=None):
        query = self.session.query(Brand)

        if searchterm:
            query = query.filter(Brand.name.ilike("%" + searchterm + "%"))
        if category_id:
            query = query.filter(Brand.category_id==category_id)
        query = query.options(joinedload(Brand.validations))
        return query.all()

    def get_brand(self, brand_id):
        if not self.has_brand(brand_id):
            raise exceptions.BrandNotFound()
        return self.session.query(Brand).filter(Brand.id==brand_id).first()

    def remove_brand(self, brand_id):
        if not self.has_brand(brand_id):
            raise exceptions.BrandNotFound()

        self.session.query(Brand).filter(Brand.id==brand_id).delete()

    def add_brand(self, brand):
        self.session.add(brand)
        self.session.commit()

    def add_brands(self, brands):
        self.session.add_all(brands)
        self.session.commit()

    def update(self, brand=None):
        brand.updated_at = datetime.now()
        self.session.commit()

    def add_brand_validation(self, brand_id, validation):
        if not self.has_brand(brand_id):
            raise exceptions.BrandNotFound()

        if self.brand_has_been_validated_by(brand_id, validation.validator.id):
            raise exceptions.BrandAlreadyValidated()

        brand = self.get_brand(brand_id)
        brand.validations += [validation]
        self.session.commit()

    def brand_has_been_validated_by(self, brand_id, validator_id):
        count = self.session.query(BrandValidation)\
            .filter(BrandValidation.validator_id==validator_id)\
            .filter(BrandValidation.brand_id==brand_id) \
            .count()
        return bool(count)

    def has_brand_validation(self, brand_validation_id):
        count = self.session.query(BrandValidation).filter(BrandValidation.id==brand_validation_id).count()
        return len(count)

    def get_brand_validation_by_validator(self, validator_id):
        return self.session.query(BrandValidation).filter(BrandValidation.validator_id==validator_id).first()

    def remove_brand_validation(self, brand_id, validator_id):
        if not self.has_brand(brand_id):
            raise exceptions.BrandNotFound()

        self.session.query(BrandValidation)\
            .filter(BrandValidation.validator_id==validator_id)\
            .filter(BrandValidation.brand_id==brand_id)\
            .delete()
        self.session.commit()

    def get_brand_validations(self, brand_id):
        if not self.has_brand(brand_id):
            raise exceptions.BrandNotFound()

        return self.session.query(BrandValidation).filter(BrandValidation.brand_id==brand_id).all()