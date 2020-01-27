from api.app import app
from api.models.event import db
from api.models.event import EventCategory


image_base_url = 'https://res.cloudinary.com/ofelix03/image/upload/v1579956502/event-categories/'
categories = [['Photography', image_base_url + 'o9efxlrvsxp1qmkdf4dd'],
              ['Sport', image_base_url + 'lfvbwr3igqqefgkfdbdp'],
              ['Education', image_base_url + 'apxizu26ftwkpjqqbicm'],
              ['Technology', image_base_url + 'uis3xyhlzlrghlli65a2'],
              ['Art & Culture', image_base_url + 'gaij4tzo7qe34xip9z8k'],
              ['Agriculture', image_base_url + 'gu8errtptdjk7wwqmfzl'],
              ['Business', image_base_url + 'sgbgutcqnhjpm4vwrkch'],
              ['Health', image_base_url + 'htmvt5mzo0cgotovtqsf'],
              ['Politics', image_base_url + 'ra6qpeifjp9jvmmqivzh']
            ]

categor_objs = []
for categ in categories:
    [name, image] = categ
    categor_objs.append(EventCategory(name=name, image=image))

with app.app_context():
    db.session.add_all(categor_objs)
    db.session.commit()