from flask import current_app as app
from utils.auth import AdminAuth
import copy
import routes.apiKeys

# copy from users schema, but remove readonly
schema = copy.deepcopy(routes.apiKeys.schema)

config = {
    'item_title': 'adminApiKey',
    'public_methods': [],
    'public_item_methods': [],
    'datasource': {
        'source': 'apiKeys'
    },
    'item_methods': ['GET', 'DELETE'],
    'resource_methods': ['GET', 'POST'],
    'schema': schema,
    'authentication': AdminAuth()
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_adminApiKeys += routes.apiKeys.onInsert
    app.on_inserted_adminApiKeys += routes.apiKeys.onInserted
