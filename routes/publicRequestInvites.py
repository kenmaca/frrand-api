from flask import current_app as app
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

    app.on_update_publicRequestInvites += onUpdate
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

        # otherwise, just sort by time
        except AttributeError:
            lookup['$orderby'] = {'_created': DESCENDING}

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
