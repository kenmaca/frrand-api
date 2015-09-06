from flask import current_app as app
from eve.methods.post import post_internal
from lib.gcm import gcmSend
from models.locations import Location
from models.users import User
from models.addresses import Address

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
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_inserted_locations += onInserted

# hooks

def onInserted(locations):
    ''' (list of dict) -> NoneType
    An Eve hook used after locations have been inserted.
    '''

    for location in locations:
        _convertToAddress(
            Location(app.data.driver.db, Location.collection, **location)
            .setCurrent()
            .mergePrevious(STATIONARY_THRESHOLD, ACCURACY)
            .buildTravelRegion(LIMIT_REGION)
            .commit()
        )

# helpers

def _convertToAddress(location):
    ''' (Location) -> NoneType
    Determines if the Location was reported enough to be considered a
    permanent address for the reporter.
    '''

    if location.get('timesReported') >= ADDRESS_THRESHOLD:
        resp = post_internal('addresses', {
            'location': location.get('location')
        })

        if resp[3] == 201:

            # set ownership of newly created Address to self
            address = (
                Address.fromObjectId(app.data.driver.db, resp[0]['_id'])
                .set('createdBy', location.get('createdBy'))
                .commit()
            )

            # alert owner that an address was created for them
            User.fromObjectId(
                app.data.driver.db,
                location.get('createdBy')
            ).message(
                'addressCreated',
                address.getId()
            )
