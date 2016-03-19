from utils.auth import UserAuth
from flask import current_app as app
import errors.apiKeys
import messages.apiKeys
import random
import string

schema = {
    'deviceId': {
        'type': 'string',
        'minlength': 10,
        'required': True
    },
    'voucher': {
        'type': 'string',
    },
    'createdBy': {
        'type': 'objectid'
    },
    'apiKey': {
        'type': 'string',
        'readonly': True
    }
}

config = {
    'item_title': 'apiKey',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'item_methods': [],
    'resource_methods': ['POST'],
    'schema': schema,
    'authentication': UserAuth()
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_apiKeys += onInsert
    app.on_inserted_apiKeys += onInserted

# hooks

# on_insert_apiKeys
def onInsert(insertApiKeys):
    ''' (list of dicts) -> NoneType
    An Eve hook used prior to insertion.
    '''

    for apiKey in insertApiKeys:
        _provision(apiKey)

# on_inserted_apiKeys
def onInserted(insertedApiKeys):
    ''' (list of dicts) -> NoneType
    An Eve hook used after insertion.
    '''

    import models.apiKeys as apiKeys
    for apiKey in insertedApiKeys:
        apiKeys.APIKey(
            app.data.driver.db,
            apiKeys.APIKey.collection,
            **apiKey
        ).prune()

# helpers

def _provision(apiKey):
    ''' (dict) -> NoneType
    Generates an apiKey for a given deviceId and user.
    '''

    token = (''.join(random.choice(string.ascii_uppercase)
        for x in range(32)))
    import models.users as users
    user = users.User.fromObjectId(
        app.data.driver.db,
        apiKey['createdBy']
    )

    # require new users to activate their accounts with a voucher/betakey
    if not user.exists('activated') or not user.get('activated'):
        try:
            import models.vouchers as vouchers
            apiKey['voucher'] = apiKey['voucher'].upper()
            voucher = vouchers.Voucher.findOne(
                app.data.driver.db,
                voucher=apiKey['voucher']
            )

            if voucher.isUsed():
                raise KeyError()

            # mark as used and activate the user account
            voucher.use(user).commit()
            (user
                .set('activated', True)
                .increment('points', voucher.getSupplement())
                .commit()
            )

        except KeyError:
            errors.apiKeys.abortInvalidVoucher()

    # only insert into MongoDB if GCM went through
    if user.message(
        *messages.apiKeys.loggedIn(
            token,
            user.getId(),
            apiKey['deviceId']
        )
    ):

        # inject generated apiKey to doc
        apiKey['apiKey'] = token
    else:
        errors.apiKeys.abortFaultyDeviceId()
