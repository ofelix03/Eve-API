from api.repositories.base import Repository

from api.models.event import SocialMedia, Country


class JobNotFound(Exception):
    pass


# class CountryRepository(Repository):

    # def has_country(self, country_id):
    #     count = self.session.query(Country).filter(Country.id==country_id).count()
    #     return bool(count)
    #
    # def has_country_by_name(self, name):
    #     count = self.session.query(Country).filter(Country.name==name).count()
    #     return bool(count)
    #
    # def get_countries(self):
    #     countries = self.session.query(Country).all()
    #     return countries
    #
    # def get_country(self, country_id):
    #     return self.session.query(Country).filter(Country.id==country_id).one()
    #
    # def get_country_by_code(self, code):
    #     return self.session.query(Country).filter(Country.code==code).one()
    #
    # def add_country(self, country):
    #     self.session.add(country)
    #     self.session.commit()
    #
    # def update_country(self):
    #     self.session.commit()
    #
    # def remove_country(self, country_id):
    #     self.session.query(Country).filter(Country.id==country_id).delete()
    #
    # def find_countries_by_searchterm(self, searchterm):
    #     if searchterm is None:
    #         return []
    #     searchterm = '%' + searchterm + '%'
    #     countries = self.session.query(Country) \
    #         .filter(Country.name.ilike(searchterm)) \
    #         .all()
    #     return countries




class GeneralRepository(CountryRepository):

    def has_social_account(self, account_id):
        count = self.session.query(SocialMedia).filter(SocialMedia.id==account_id).count()
        return count

    def get_social_account(self, account_id):
        return self.session.query(SocialMedia).filter(SocialMedia.id==account_id).first()


