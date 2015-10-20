from flask import current_app as app
from eve.methods.post import post_internal
import messages.locations

# the number of times a location needs to be reported in a row
# to be considered a stationary location
STATIONARY_THRESHOLD = 3

# the number of times a stationary location needs to be reported
# to be considered as a permanent address on record
ADDRESS_THRESHOLD = 6

# the maximum number of points to consider for a user's travel region
LIMIT_REGION = 5

# the degree of accuracy of each coordinate pair reported
ACCURACY = 4

schema = {
    'location': {
        'type': 'point',
        'required': True
    },
    'dayOfWeek': {
        'type': 'integer',
        'min': 1,
        'max': 7,
        'readonly': True
    },
    'hour': {
        'type': 'integer',
        'min': 0,
        'max': 23,
        'readonly': True
    },
    'timesReported': {
        'type': 'integer',
        'readonly': True,
        'default': 1
    },
    'region': {
        'type': 'polygon',
        'readonly': True
    },
    'current': {
        'type': 'boolean',
        'readonly': True,
        'default': True
    }
}

config = {
    'item_title': 'location',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'mongo_indexes': {
        '_id_': [('_id', 1)],
        'location_2dsphere': [('location', '2dsphere')],
        'region_2dsphere': [('region', '2dsphere')]
    },
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_inserted_locations += onInserted

# hooks

def onInserted(insertedLocations):
    ''' (list of dict) -> NoneType
    An Eve hook used after locations have been inserted.
    '''

    import models.locations as locations
    for location in insertedLocations:
        if 'createdBy' in location:
            _generateTemporaryAddress(
                _convertToAddress(
                    locations.Location(
                        app.data.driver.db,
                        locations.Location.collection,
                        **location
                    ).setCurrent()
                    .mergePrevious(STATIONARY_THRESHOLD, ACCURACY)
                    .buildTravelRegion(LIMIT_REGION)
                    .commit()
                )
            )

# helpers

def _convertToAddress(location):
    ''' (models.location.Location) -> models.location.Location
    Determines if the Location was reported enough to be considered a
    permanent address for the reporter.
    '''

    if location.get('timesReported') >= ADDRESS_THRESHOLD:
        resp = post_internal('addresses', {
            'location': location.get('location')
        })

        if resp[3] == 201:

            # set ownership of newly created Address to self
            import models.addresses as addresses
            address = (
                addresses.Address.fromObjectId(
                    app.data.driver.db,
                    resp[0]['_id']
                ).set('createdBy', location.get('createdBy'))
                .commit()
            )

            # alert owner that an address was created for them
            import models.users as users
            users.User.fromObjectId(
                app.data.driver.db,
                location.get('createdBy')
            ).message(
                *messages.locations.created(address.getId())
            )

    return location

def _generateTemporaryAddress(location):
    ''' (models.location.Location) -> models.location.Location
    Attempts to generate a temporary Address if there are currently
    no permanent Addresses for the User that the location belongs to.
    '''

    import models.addresses as addresses
    if not location.getOwner().getAddresses():
        query = {'location': location.get('location')}

        # try to see if there was a temporary address for this location
        # and inject address in if there was
        try:
            query['address'] = addresses.Address.findOne(
                app.data.driver.db,
                **{
                    'createdBy': location.getOwner().getId(),
                    'location': location.get('location')
                }
            ).get('address')
        except KeyError:
            pass

        resp = post_internal('addresses', query)

        if resp[3] == 201:

            # set ownership of address and temporary status
            address = (
                addresses.Address.fromObjectId(
                    app.data.driver.db,
                    resp[0]['_id']
                ).set('createdBy', location.getOwner().getId())
                .set('temporary', True)
            ).commit()

            # alert owner that an address was created for them
            location.getOwner().message(
                *messages.requests.created(address.getId())
            )

    return location
