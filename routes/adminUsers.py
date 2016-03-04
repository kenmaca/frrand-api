from flask import current_app as app
from utils.auth import AdminAuth
import routes.users
import errors.users

config = {
    'item_title': 'adminUser',
    'public_methods': [],
    'public_item_methods': [],
    'datasource': {
        'source': 'users'
    },
    'extra_response_fields': ['username'],
    'item_methods': ['GET', 'PATCH', 'DELETE'],
    'resource_methods': ['GET', 'POST'],
    'schema': routes.users.schema,
    'authentication': AdminAuth()
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_adminUsers += routes.users.onInsert
    app.on_inserted_adminUsers += routes.users.onInserted
    app.on_updated_adminUsers += routes.users.onUpdated
    app.on_update_adminUsers += routes.users.onUpdate
