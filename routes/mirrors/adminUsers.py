from flask import current_app as app
from utils.auth import AdminAuth
import copy
import routes.users

# copy from users schema, but remove readonly
schema = copy.deepcopy(routes.users.schema)
schema['points']['readonly'] = False
schema['pendingPoints']['readonly'] = False
schema['activated']['readonly'] = False
schema['phoneVerified']['readonly'] = False
schema['isAdmin']['readonly'] = False
schema['facebookId']['readonly'] = False
schema['rating']['readonly'] = False
schema['numberOfRatings']['readonly'] = False

config = {
    'item_title': 'adminUser',
    'public_methods': [],
    'public_item_methods': [],
    'datasource': {
        'source': 'users'
    },
    'extra_response_fields': ['username'],
    'item_methods': ['GET', 'PATCH', 'DELETE'],
    #'pagination_limit': 500,
    'pagination': False,
    'resource_methods': ['GET', 'POST'],
    'schema': schema,
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
