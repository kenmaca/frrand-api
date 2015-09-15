from flask import current_app as app
import errors.publicRequestInvites

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

    app.on_update_publicRequestInvites += onUpdate
    app.on_fetched_item_publicRequestInvites += onFetchedItem
    app.on_fetched_resource_publicRequestInvites += onFetched

# on_fetched_item_publicRequestInvites
def onFetchedItem(publicInvite):
    ''' (dict) -> NoneType
    An Eve hook used to embed requests to its child requestInvites as
    well as to convert all times to strings in RFC-1123 standard.
    '''

    import models.publicRequestInvites as publicRequestInvites
    publicInvite.update(
        publicRequestInvites.PublicInvite(
            app.data.driver.db,
            publicRequestInvites.PublicInvite.collection,
            **publicInvite
        ).embedView()
    )

# on_fetched_resource_publicRequestInvites
def onFetched(publicInvites):
    ''' (dict) -> NoneType
    An Eve hook used during fetching a list of publicRequestInvites.
    '''

    # embed each publicRequestInvite
    if '_items' in publicInvites:
        for publicInvite in publicInvites['_items']:
            onFetchedItem(publicInvite)

# on_update_publicRequestInvites
def onUpdate(changes, publicInvite):
    ''' (dict, dict) -> NoneType
    An Eve hook used prior to a publicRequestInvite is updated.
    '''

    if 'acceptedBy' in changes:
        import models.publicRequestInvites as publicRequestInvites
        _createAcceptedInvite(
            publicRequestInvites.PublicInvite.fromObjectId(
                app.data.driver.db,
                publicInvite['_id']
            )
        )

# helpers

def _createAcceptedInvite(publicInvite):
    ''' (models.publicRequestInvite.PublicInvite) -> NoneType
    Creates an pre-accepted Invite.
    '''

    try:
        import models.requests as requests
        request = requests.Request.findOne(
            app.data.driver.db,
            _id=publicInvite.get('requestId'),
            publicRequestInviteId=publicInvite.getId()
        )

        if publicInvite.get('acceptedBy'):

            # adding candidate to prep generation of invite
            request.push('candidates', publicInvite.get('acceptedBy')).commit()

            # generate invites
            import routes.requests as requestsRoute
            requestsRoute._generateRequestInvites(request)
    
            # set accepted on the newly generated invite
            import models.requestInvites as requestInvites
            requestInvites.Invite.findOne(
                app.data.driver.db,
                requestId=request.getId()
            ).accept().commit()

            # finally, allow others to accept this PublicInvite too
            publicInvite.set('acceptedBy', None).commit()

    except KeyError:
        errors.publicRequestInvites.abortUnknownRequest()
