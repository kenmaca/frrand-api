from utils.auth import GenerateVoucherAuth
from flask import current_app as app
from datetime import datetime
from pytz import UTC
import random
import string

schema = {
    'voucher': {
        'type': 'string',
        'minlength': 1,
        'unique': True
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
        'default': 1,
        'min': 1
    },
    'pointSupplement': {
        'type': 'integer',
        'default': 0
    },
    'groupAttach': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'groups',
            'field': '_id'
        }
    },
    'starts': {
        'type': 'datetime',
        'default': datetime.utcnow().replace(tzinfo=UTC)
    },
    'ends': {
        'type': 'datetime',
    }
}

config = {
    'item_title': 'voucher',
    'public_methods': ['POST', 'GET'],
    'public_item_methods': [],
    'allowed_filters': [],
    'item_methods': [],
    'resource_methods': ['POST', 'GET'],
    'auth_field': None,
    'authentication': GenerateVoucherAuth(),
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_vouchers += onInsert

# hooks

# on_insert_beta
def onInsert(insertVouchers):
    ''' (list of dicts) -> NoneType
    An Eve hook used prior to insertion.
    '''

    for voucher in insertVouchers:
        if 'voucher' not in voucher:
            voucher['voucher'] = (
                ''.join(
                    random.choice(string.ascii_uppercase)
                    for x in range(6)
                )
            )
        else:

            # force uppercase
            voucher['voucher'] = voucher['voucher'].upper()
