from flask import current_app as app
from utils.auth import AdminAuth
import copy
import routes.addresses

# copy from addresses schema, but remove readonly
schema = copy.deepcopy(routes.addresses.schema)

config = {
    'item_title': 'adminAddresses',
    'public_methods': [],
    'public_item_methods': [],
    'datasource': {
        'source': 'addresses'
    },
    'item_methods': ['GET', 'PATCH', 'DELETE'],
    'resource_methods': ['GET', 'POST'],
    'mongo_indexes': {
        '_id_': [('_id', 1)],
        'location_2dsphere': [('location', '2dsphere')]
    },
    'schema': schema,
    'authentication': AdminAuth()
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_inserted_adminAddresses += routes.addresses.onInserted
    app.on_updated_adminAddresses += routes.addresses.onUpdated
