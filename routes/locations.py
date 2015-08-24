from datetime import datetime

schema = {
    'location': {
        'type': 'point',
        'required': True
    },
    'dayOfWeek': {
        'type': 'integer',
        'min': 1,
        'max': 7
    },
    'hour': {
        'type': 'integer',
        'min': 0,
        'max': 23
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

    app.on_insert_locations += supplementLocationData

# hooks

# on_insert_locations
def supplementLocationData(locations):
    ''' (dict) -> NoneType
    An Eve hook used to add dayOfWeek and hour data as well as
    approximate longitude and latitude within 11 metres.
    '''

    for location in locations:

        # location grid datetime injection if not provided
        if 'dayOfWeek' not in location:
            location['dayOfWeek'] = datetime.utcnow().isoweekday()
        if 'hour' not in location:
            location['hour'] = datetime.utcnow().hour

        # approximate coordinates
        location['location']['coordinates'] = [round(point, 4)
            for point in location['location']['coordinates']]
