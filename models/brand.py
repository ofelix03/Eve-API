# import uuid
# from datetime import datetime
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric, Table
# from sqlalchemy.orm import relationship
#
# from api import db
# from api.models.event import User
#
# Base = declarative_base()
#
# CASCADE = 'CASCADE'
#
# session = db.Session()
#
#
# class BrandCategory(Base):
#     __tablename__ = 'brand_categories'
#
#     id = Column(String, primary_key=True)
#     name= Column(String)
#     brands = relationship('Brand', backref='brand_categories')
#
#
# class Brand(Base):
#     __tablename__ = 'brands'
#
#     id = Column(String, primary_key=True)
#     name = Column(String)
#     description = Column(String)
#     country = Column(String)
#     image = Column(String)
#     created_at = Column(DateTime)
#     updated_at = Column(DateTime)
#     creator = relationship(User)
#     creator_id = Column(String, ForeignKey('users.id'))
#     category = relationship('BrandCategory')
#     category_id = Column(String, ForeignKey('brand_categories.id', ondelete=CASCADE, onupdate=CASCADE))
#
