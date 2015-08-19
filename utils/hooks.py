from lib.gcm import gcmSend
from flask import abort
from flask import current_app as app
from eve.methods.post import post_internal
from datetime import datetime, timedelta
import random
import string

def provisionApiKey(apiKeys):
    ''' (dict) -> NoneType
    An Eve hook used to generate an apiKey from a document that is about
    to be inserted containing a deviceId.

    REQ: documents was inserted via an Authenticated route,
    dependant on the createdBy auth_field
    '''

    for key in apiKeys:
        apiKey = (''.join(random.choice(string.ascii_uppercase)
            for x in range(32)))

        # only insert into MongoDB if GCM went through
        if (gcmSend(key['deviceId'], {
            'type': 'apiKey',
            'apiKey': apiKey
        })):

            # inject generated apiKey to doc
            key['apiKey'] = apiKey
        else:
            abort(422)

def initNewUser(users):
    ''' (dict) -> NoneType
    An Eve hook used to set the createdBy field for an newly
    inserted user document to itself (since Eve handles
    auth_field only when inserting via Authenticated routes).
    '''

    for user in users:

        # set newly created user as self-owning
        app.data.driver.db['users'].update({
            '_id': user['_id']
        }, {
            '$set': {
                'createdBy': user['_id']
            }
        }, upsert=False, multi=False)

        # and finally, create a new apiKey and self-owning
        with app.test_request_context():
            post_internal('apiKeys', {
                'deviceId': user['deviceId'],
                'createdBy': user['_id']
            })

def generateRequestInvites(requests):
    ''' (dict) -> NoneType
    An Eve hook used to automatically generate RequestInvites for
    the given Requests and sends out the RequestInvite via GCM.
    '''

    # currently just sends out to ALL users (for dev use only)
    # TODO: perform candidate matching here
    users = app.data.driver.db['users'].find({})
    for request in requests:
        for user in users:
            with app.test_request_context():
                post_internal('requestInvites', {
                    'requestId': request['_id'],
                    'location': {
                        'type': 'Point',
                        'coordinates': [0.0, 0.0]
                    },
                    'from': request['createdBy'],
                    'createdBy': user['_id']
                })

def requestInviteSendGcm(requestInvites):
    ''' (dict) -> NoneType
    An Eve hook used to send out requestInvites via GCM.
    '''

    for requestInvite in requestInvites:

        # first, add to list of invites for parent request
        app.data.driver.db['requests'].update(
            {'_id': requestInvite['requestId']},
            {'$push': {'inviteIds': requestInvite['_id']}}
        )

        # send gcm
        deviceIds = app.data.driver.db['apiKeys'].find({
            'createdBy': requestInvite['createdBy']
        }).sort('_id', -1).limit(1)

        for deviceId in deviceIds:
            gcmSend(deviceId['deviceId'], {
                'type': 'requestInvite',
                'requestInvite': requestInvite
            })

def requestInviteExpiry(requestInvites):
    ''' (dict) -> NoneType
    An Eve hook used to add an expiry time of 1 minute to each
    requestInvite.
    '''

    for requestInvite in requestInvites:
        requestInvite['requestExpiry'] = datetime.utcnow() + timedelta(
            minutes=1
        )

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

def pruneStaleApiKeys(apiKeys):
    ''' (dict) -> NoneType
    An Eve hook used to remove any other apiKeys with the same
    deviceId as newly inserted ones to maintain a 1-to-1 pairing
    of deviceIds to apiKeys.
    '''

    for apiKey in apiKeys:
        app.data.driver.db['apiKeys'].remove({
            'deviceId': apiKey['deviceId']
        })
