from flask import current_app as app
from flask import abort
from models.requests import Request
from models.requestInvites import Invite
from models.publicRequestInvites import PublicInvite
from routes.requests import _generateRequestInvites

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
    app.on_pre_GET_publicRequestInvites += onPreGet
    app.on_fetched_item_publicRequestInvites += onFetchedItem

# on_pre_GET_publicRequestInvites
def onPreGet(request, lookup):
    ''' (dict, dict) -> NoneType
    An Eve hook used prior to a GET request.
    '''

    if '_id' in lookup:

        # update last updated to trigger fresh fetch each time
        (PublicInvite.fromObjectId(app.data.driver.db, lookup['_id'])
            .set('_updated': datetime.utcnow()).commit()
        )

# on_fetched_item_publicRequestInvites
def onFetchedItem(publicInvite):
    ''' (dict) -> NoneType
    An Eve hook used to embed requests to its child requestInvites as
    well as to convert all times to strings in RFC-1123 standard.
    '''

    publicInvite.update(
        PublicInvite(
            app.data.driver.db,
            PublicInvite.collection,
            **publicInvite
        ).embedView()
    )

# on_updated_publicRequestInvites
def onUpdated(changes, publicInvite):
    ''' (dict, dict) -> NoneType
    An Eve hook used after a publicRequestInvite is updated.
    '''

    if 'acceptedBy' in changes:
        _convertToAcceptedInvite(
            PublicInvite.fromObjectId(publicInvite['_id'])
        )

# helpers

def _createAcceptedInvite(publicInvite):
    ''' (models.publicRequestInvite.PublicInvite) -> NoneType
    Creates an pre-accepted Invite.
    '''

    try:
        request = Request.findOne(
            app.data.driver.db,
            _id=publicInvite.get('requestId'),
            publicRequestInviteId=publicInvite.getId()
        )

        if publicInvite.get('acceptedBy'):

            # adding candidate to prep generation of invite
            request.push('candidate', publicInvite.get('acceptedBy')).commit()

            # generate invites
            _generateRequestInvites(request)
    
            # set accepted on the newly generated invite
            Invite.findOne(
                app.data.driver.db,
                requestId=request.getId()
            ).accept().commit()

            # finally, allow others to accept this PublicInvite too
            publicInvite.set('acceptedBy', None).commit()

    except KeyError:
        abort(422)