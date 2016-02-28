from utils.auth import GenerateBetaKeyAuth
from flask import current_app as app, abort
import random
import string

schema = {
    'betaKey': {
        'type': 'string'
    },
    'usedBy': {
        'type': 'list',
        'default': [],
        'readonly': True,
        'schema': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'users',
                'field': '_id'
            }
        }
    },
    'limit': {
        'type': 'integer',
        'default': 1
    },
    'pointSupplement': {
        'type': 'integer',
        'default': 0
    }
}

config = {
    'item_title': 'beta',
    'public_methods': ['POST', 'GET'],
    'public_item_methods': [],
    'allowed_filters': [],
    'item_methods': [],
    'resource_methods': ['POST', 'GET'],
    'auth_field': None,
    'authentication': GenerateBetaKeyAuth(),
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_beta += onInsert

# hooks

# on_insert_beta
def onInsert(insertBeta):
    ''' (list of dicts) -> NoneType
    An Eve hook used prior to insertion.
    '''

    for beta in insertBeta:
        if 'betaKey' not in beta:
            beta['betaKey'] = (
                ''.join(
                    random.choice(string.ascii_uppercase)
                    for x in range(6)
                )
            )
