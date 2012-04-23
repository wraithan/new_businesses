from datetime import date, timedelta
import json

import requests
from geoloqi.geoloqi import Geoloqi
from dateutil import parser


geo = Geoloqi()
businesses_url = \
    "http://api.civicapps.org/business-licenses/category/%s?since=%s"
six_months = timedelta(days=180)
six_months_ago = date.today()-six_months
message = '%s applied for their business licence on %s, they are located at: %s'

def create_layers():
    layer_list = None
    with open('layers.json') as f:
        layer_list = json.loads(f.read())
        for index,layer in enumerate(layer_list['layers']):
            res = geo.post('layer/create', {
                'name': 'New Businesses (%s)' % layer['description'].strip(),
                'key': str(layer['description']),
                'description': 'Show new %s businesses.' % (
                    layer['description'].strip().lower()
                ),
                'public': 1
            })
            layer_list['layers'][index]['layer_id'] = res['layer_id']
    with open('new_layers.json', 'w') as f:
        f.write(json.dumps(layer_list, indent=2))

def update_all_layers():
    with open('layers.json') as f:
        layer_list = json.loads(f.read())
        for layer in layer_list['layers']:
            print layer['description']
            for naics in layer['naics_id']:
                update_layer(layer['layer_id'], naics)

def update_layer(layer_id, naics_id):
    res = requests.get(businesses_url % (naics_id, six_months_ago))
    try:
        businesses = json.loads(res.text)
    except ValueError:
        # This happens when the category isn't valid. I got the
        # categories from the site so I trust they exist, but when
        # they don't I want to fail out.
        return
    if not isinstance(businesses, list):
        for biz in businesses['results']:
            geo_res = geo.post('trigger/create', {
                'place_layer_id': layer_id,
                'latitude': biz['Latitude'],
                'longitude': biz['Longitude'],
                'place_name': biz['BusinessName'],
                'key': biz['Privacyid'],
                'place_key': biz['Privacyid'],
                'radius': 240,
                'type': 'message',
                'text': message % (
                    biz['BusinessName'],
                    biz['DateAdded'],
                    biz['GISAddress']
                ),
                'date_to': str(
                    parser.parse(biz['DateAdded']).date() + six_months
                ),
                'one_time': 1
            })

update_all_layers()