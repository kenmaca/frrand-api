from flask import current_app as app, g
import errors.publicRequestInvites
from pymongo import DESCENDING

schema = {
    'requestId': {
        'type': 'objectid',
        'required': True,
        'data_relation': {
            'resource': 'requests',
            'field': '_id'
        }
    },
    'acceptedBy': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'users',
            'field': '_id'
        },
        'default': None
    },
    'acceptedByCurrentUser': {
        'type': 'boolean',
        'readonly': True
    },
    'location': {
        'type': 'point',
        'readonly': True
    }
}

config = {
    'item_title': 'publicRequestInvite',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH'],
    'mongo_indexes': {
        '_id_': [('_id', 1)],
        'location_2dsphere': [('location', '2dsphere')]
    },
    'schema': schema,
    'auth_field': None
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_updated_publicRequestInvites += onUpdated
    app.on_fetched_item_publicRequestInvites += onFetchedItem
    app.on_fetched_resource_publicRequestInvites += onFetched
    app.on_pre_GET_publicRequestInvites += onPreGet

# on_pre_GET_publicRequestInvites
def onPreGet(request, lookup):
    ''' (dict) -> NoneType
    An Eve hook used before a GET request.
    '''

    # if resource level GET, then sort and filter by proximity
    if '_id' not in lookup:
        import models.users as users

        # add proximity sorting if location exists
        try:
            lookup['location'] = {
                '$near': {
                    '$geometry': users.getCurrentUser(
                        app.data.driver.db
                    ).getLastLocation().getGeo(),
                }
            }

        except AttributeError:
            pass

# on_fetched_item_publicRequestInvites
def onFetchedItem(publicInvite):
    ''' (dict) -> NoneType
    An Eve hook used to embed requests to its child requestInvites as
    well as to convert all times to strings in RFC-1123 standard.
    '''

    import models.publicRequestInvites as publicRequestInvites
    public = publicRequestInvites.PublicInvite(
        app.data.driver.db,
        publicRequestInvites.PublicInvite.collection,
        **publicInvite
    )
    publicInvite.update(public.embedView())

    # inject into view to show if current user has accepted this invite
    publicInvite['acceptedByCurrentUser'] = g.get('auth_value') in [
        invite.getOwner().getId()
        for invite in public.getRequest().getInvites()
    ]

    # remove redundant location data (used for internal sorting)
    if 'location' in publicInvite:
        del publicInvite['location']

# on_fetched_resource_publicRequestInvites
def onFetched(publicInvites):
    ''' (dict) -> NoneType
    An Eve hook used during fetching a list of publicRequestInvites.
    '''

    # embed each publicRequestInvite
    if '_items' in publicInvites:
        for publicInvite in publicInvites['_items']:
            onFetchedItem(publicInvite)

# on_updated_publicRequestInvites
def onUpdated(changes, publicInvite):
    ''' (dict, dict) -> NoneType
    An Eve hook used after a publicRequestInvite is updated.
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
        if publicInvite.get('acceptedBy'):
            request = publicInvite.getRequest()

            # adding candidate to prep generation of invite
            try:
                request.addCandidate(publicInvite.get('acceptedBy')).commit()
            except ValueError:
                errors.publicRequestInvites.abortDuplicateCandidate()

            # generate invites
            import routes.requests as requestsRoute
            requestsRoute._generateRequestInvites(request)
    
            # set accepted on the newly generated invite
            import models.requestInvites as requestInvites
            try:
                requestInvites.Invite.findOne(
                    app.data.driver.db,
                    requestId=request.getId(),
                    createdBy=publicInvite.get('acceptedBy')
                ).accept().commit()
            except KeyError:
                pass

            # finally, allow others to accept this PublicInvite too
            publicInvite.set('acceptedBy', None).commit()

    except KeyError:
        errors.publicRequestInvites.abortUnknownRequest()
