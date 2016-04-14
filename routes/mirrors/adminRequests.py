from flask import current_app as app
from utils.auth import AdminAuth
import copy
import routes.requests

# copy from users schema, but remove readonly
schema = copy.deepcopy(routes.requests.schema)
schema['candidates']['readonly'] = False
schema['publicRequestInviteId']['readonly'] = False
schema['pickedUp']['readonly'] = False
schema['isMutuallyCancelled']['readonly'] = False
schema['numberOfComments']['readonly'] = False

config = {
    'item_title': 'adminRequest',
    'public_methods': [],
    'public_item_methods': [],
    'datasource': {
        'source': 'requests'
    },
    #'extra_response_fields': ['username'],
    'item_methods': ['GET', 'PATCH', 'DELETE'],
    'pagination': False,
    'allowed_filters': ['*'],
    'resource_methods': ['GET', 'POST'],
    'schema': schema,
    'authentication': AdminAuth()
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_adminRequests += routes.requests.onInsert
    app.on_inserted_adminRequests += routes.requests.onInserted
    app.on_fetched_item_adminRequests += routes.requests.onFetchedItem
    app.on_fetched_resource_adminRequests += routes.requests.onFetched
    app.on_update_adminRequests += routes.requests.onUpdate
    app.on_updated_adminRequests += routes.requests.onUpdated