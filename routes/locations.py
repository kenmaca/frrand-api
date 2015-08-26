from datetime import datetime
from flask import current_app as app
from pymongo import DESCENDING
from eve.methods.post import post_internal
from lib.gcm import gcmSend

# the number of times a location needs to be reported in a row
# to be considered a stationary location
STATIONARY_THRESHOLD = 3

# the number of times a stationary location needs to be reported
# to be considered as a permanent address on record
ADDRESS_THRESHOLD = 6

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
    },
    'timesReported': {
        'type': 'integer',
        'readonly': True,
        'default': 1
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

    app.on_insert_locations += onInsert

# hooks

def onInsert(locations):
    ''' (list of dict) -> NoneType
    An Eve hook used prior to inserting locations.
    '''

    for location in locations:
        _supplementLocationData(location)
        _mergePrevious(location)
        _convertToAddress(location)

# helpers

def _supplementLocationData(location):
    ''' (dict) -> NoneType
    Adds dayOfWeek and hour to the location and
    approximates longitude and latitude within 11 metres.
    '''

    # location grid datetime injection if not provided
    if 'dayOfWeek' not in location:
        location['dayOfWeek'] = datetime.utcnow().isoweekday()
    if 'hour' not in location:
        location['hour'] = datetime.utcnow().hour

    # approximate coordinates
    location['location']['coordinates'] = [round(point, 4)
        for point in location['location']['coordinates']]

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

# on_insert_locations
def _mergePrevious(location):
    ''' (dict) -> NoneType
    Converts a regular reported location to a stationary
    one if the location was reported STATIONARY_THRESHOLD times in a row,
    or increments the timesReported if there is currently already a stationary
    location for these coordinates.

    REQ: _supplementLocationData is performed beforehand
    '''

    # check if there is already a stationary location for these coordinates
    stationary = app.data.driver.db['locations'].find_one(
        {
            'hour': location['hour'],
            'dayOfWeek': location['dayOfWeek'],
            'location.coordinates': location['location']['coordinates'],
            'timesReported': {
                '$gt': 1
            },
            'createdBy': location['createdBy']
        }
    )

    if stationary:

        # merge with stationary and remove older location
        location['timesReported'] += stationary['timesReported']
        app.data.driver.db['locations'].remove(stationary['_id'])

    else:

        # never stationary, so check if it is now
        lastReportedLocations = app.data.driver.db['locations'].find(
            {'createdBy': location['createdBy']}
        ).sort('_id', DESCENDING).limit(STATIONARY_THRESHOLD)

        timesReported = 0
        if lastReportedLocations:
            for lastReported in lastReportedLocations:
                if lastReported['location'] == location['location']:
                    timesReported += lastReported['timesReported']
                else:

                    # exit prematurely if the chain is broken
                    break

        # if stationary, then merge all previous locations from this
        # timeblock cell with the same coordinates
        if timesReported + 1 >= STATIONARY_THRESHOLD:
            locationsToMerge = app.data.driver.db['locations'].find(
                {
                    'hour': location['hour'],
                    'dayOfWeek': location['dayOfWeek'],
                    'location.coordinates': 
                        location['location']['coordinates'],
                    'createdBy': location['createdBy']
                }
            )

            # merge timesReported with this location and remove older doc
            if locationsToMerge:
                for merge in locationsToMerge:
                    location['timesReported'] += merge['timesReported']
                    app.data.driver.db['locations'].remove(merge['_id'])

        # otherwise, simply allow insert

def _convertToAddress(location):
    ''' (dict) -> NoneType
    Determines if this location was reported enough to be considered a permanent
    address for the reporter.

    REQ: _mergePrevious was performed beforehand
    '''

    if location['timesReported'] >= ADDRESS_THRESHOLD:
        resp = post_internal('addresses', {
            'location': location['location']
        })

        if resp[3] == 201:

            # set ownership of invite to invitee
            app.data.driver.db['addresses'].update(
                {'_id': resp[0]['_id']},
                {'$set': {'createdBy': location['createdBy']}},
                upsert=False, multi=False
            )

            # alert owner that an address was created for them
            user = app.data.driver.db['users'].find_one(
                {'_id': location['createdBy']}
            )

            gcmSend(user['deviceId'], {
                'type': 'addressCreated',
                'addressCreated': resp[0]['_id']
            })
