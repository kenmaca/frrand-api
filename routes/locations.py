from flask import current_app as app
import messages.locations

# the number of times a location needs to be reported in a row
# to be considered a stationary location
STATIONARY_THRESHOLD = 3

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
            (
                locations.Location(
                    app.data.driver.db,
                    locations.Location.collection,
                    **location
                ).setCurrent()
                .mergePrevious(STATIONARY_THRESHOLD, ACCURACY)
                .buildTravelRegion(LIMIT_REGION)
                .commit()
            )
