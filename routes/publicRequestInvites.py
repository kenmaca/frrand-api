from flask import current_app as app
from flask import abort
from eve.methods.patch import patch_internal

# add attribute to convert into an accepted requestInvite
schema = {
    'requestId': {
        'type': 'objectid',
        'required': True,
        'data_relation': {
            'resource': 'requests',
            'field': '_id'
        }
    },
    'from': {
        'type': 'objectid',
        'required': True,
        'data_relation': {
            'resource': 'users',
            'field': '_id'
        }
    },
    'phone': {
        'type': 'string'
    },
    'phoneMethods': {
        'type': 'list',
        'allowed': [
            'sms',
            'phone'
        ],
        'dependencies': [
            'phone'
        ]
    },
    'acceptedBy': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'users',
            'field': '_id'
        },
        'default': None
    }
}

config = {
    'item_title': 'publicRequestInvite',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH'],
    'schema': schema,
    'auth_field': None
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_updated_publicRequestInvites += onUpdated

# on_pre_GET_publicRequestInvites
def onPreGet(request, lookup):
    ''' (dict, dict) -> NoneType
    An Eve hook used prior to a GET request.
    '''

    pass

# on_updated_publicRequestInvites
def onUpdated(changes, publicRequestInvite):
    ''' (dict, dict) -> NoneType
    An Eve hook used after a publicRequestInvite is updated.
    '''

    print('updated')
    _convertToAcceptedInvite(changes, publicRequestInvite)

# helpers

def _convertToAcceptedInvite(changes, publicRequestInvite):
    ''' (dict, dict) -> NoneType
    Converts an unclaimed publicRequestInvite to an accepted requestInvite.
    '''

    # ensure that parent request is really attached to this public
    # request before doing anything
    request = app.data.driver.db['requests'].find_one({
        '_id': publicRequestInvite['requestId'],
        'publicRequestInviteId': publicRequestInvite['_id']
    })

    print(changes)

    if request:
        if 'acceptedBy' in changes:

            print('public invite accepted')

            # since candidates is readonly, hacky way of adding candidate
            app.data.driver.db['requests'].update(
                {'_id': request['_id']},
                {
                    '$set': {'publicRequestInviteId': None},
                    '$push': {'candidates': changes['acceptedBy']}
                },
                upsert=False, multi=False
            )

            print('mongo op internal, now external')

            # and then let patch_internal handle the generation of invites
            resp = patch_internal('requests',
                {'inviteIds': []},
                _id=request['_id']
            )

            print(resp)

            if resp[3] == 200:

                # now delete this publicInviteRequest since we have
                # an candidate that accepted the request on their own
                app.data.driver.db['publicRequestInvites'].remove({
                    '_id': publicRequestInvite['_id']
                })

                # and finally, set accepted on the (assuming single, since 
                # previously public) newly generated invite
                requestInvite = app.data.driver.db['requestInvites'].find_one({
                    'requestId': request['_id']
                })

                if requestInvite:
                    patch_internal('requestInvites',
                        {'accepted': True},
                        _id=requestInvite['_id']
                    )
    else:
        abort(422)
