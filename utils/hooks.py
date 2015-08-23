from lib.gcm import gcmSend
from flask import abort
from flask import current_app as app
from eve.methods.post import post_internal
from datetime import datetime, timedelta
from pytz import UTC
from bson import ObjectId, json_util
import json
import random
import string

# user hooks

# on_insert_apiKeys
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

# on_insert_apiKeys
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

# on_inserted_users
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

# request hooks

# on_pre_GET_requests
def forceFetchNewRequests(request, lookup):
    ''' (Request, dict) -> NoneType
    An Eve hook used to force a fresh fetch when requesting a
    request document.
    '''

    if '_id' in lookup:

        # update last updated to trigger fresh fetch each time
        res = app.data.driver.db['requests'].update(
            {'_id': ObjectId(lookup['_id'])},
            {'$set': {'_updated': datetime.utcnow()}},
            upsert=False, multi=False
        )

# on_fetched_item_requests
def embedRequestDisplay(request):
    ''' (dict) -> NoneType
    An Eve hook used to embed requestInvites to its parent request
    as well as prune the expired and unaccepted invites.
    '''

    pendingInvites = []
    if 'inviteIds' in request:
        for inviteId in request['inviteIds']:
            requestInvite = app.data.driver.db['requestInvites'].find_one({
                '_id': inviteId
            })

            # not accepted and expired, so remove the requestInvite
            if ((requestInvite['requestExpiry']
                < datetime.utcnow().replace(tzinfo=UTC))
                and (not requestInvite['accepted'])
            ):

                # remove actual requestInvite
                app.data.driver.db['requestInvites'].remove({
                    '_id': inviteId
                })
            else:
                pendingInvites.append(requestInvite)

        # update list of tracked requestInvites in parent request
        app.data.driver.db['requests'].update(
            {'_id': request['_id']},
            {'$set': {'inviteIds': 
                [invite['_id'] for invite in pendingInvites]
            }},
            upsert=False, multi=False
        )

        # finally, replace output list of invites with embedded ones
        request['inviteIds'] = pendingInvites

# on_pre_GET_requestInvites
def forceFetchNewRequestInvites(request, lookup):
    ''' (Request, dict) -> NoneType
    An Eve hook used to force a fresh fetch when requesting a
    requestInvite document.
    '''

    if '_id' in lookup:

        # update last updated to trigger fresh fetch each time
        res = app.data.driver.db['requestInvites'].update(
            {'_id': ObjectId(lookup['_id'])},
            {'$set': {'_updated': datetime.utcnow()}},
            upsert=False, multi=False
        )

# on_fetched_item_requestInvites
def embedRequestInviteDisplay(request):
    ''' (dict) -> NoneType
    An Eve hook used to embed requests to its child requestInvites as
    well as to convert all times to strings in RFC-1123 standard.
    request is mutated with new values.
    '''

    # embed parent request
    request['requestId'] = app.data.driver.db['requests'].find_one(
        {'_id': request['requestId']}
    )

    # embed from (only username here, do not provide entire document)
    request['from'] = app.data.driver.db['users'].find_one(
        {'_id': request['from']}
    )['username']

# on_inserted_requests
def generateRequestInvites(requests):
    ''' (dict) -> NoneType
    An Eve hook used to automatically generate RequestInvites for
    the given Requests and sends out the RequestInvite via GCM.
    '''

    invitesGenerated = []

    # currently just sends out to ALL users (for dev use only)
    # TODO: perform candidate matching here
    users = app.data.driver.db['users'].find({})
    for request in requests:
        for user in users:
            with app.test_request_context():

                # adding to list of inviteIds is dependant on
                # on_inserted_requestInvites to get _id
                resp = post_internal('requestInvites', {
                    'requestId': request['_id'],
                    'location': {
                        'type': 'Point',
                        'coordinates': [0.0, 0.0]
                    },
                    'from': request['createdBy']
                })

                # set ownership of invite to invitee
                app.data.driver.db['requestInvites'].update(
                    {'_id': resp[0]['_id']},
                    {'$set': {'createdBy': user['_id']}},
                    upsert=False, multi=False
                )

                # get updated requestInvite
                requestInvite = app.data.driver.db['requestInvites'].find_one(
                    {'_id': resp[0]['_id']}
                )

                # add this invite to the parent request list
                invitesGenerated.append(requestInvite['_id'])

                # embed parent request to the newly created requestInvite
                embedRequestInviteDisplay(requestInvite)

                # and finally, send gcm out
                gcmSend(user['deviceId'], {
                    'type': 'requestInvite',
                    'requestInvite': requestInvite
                })

        # update list of inviteIds in Mongo
        app.data.driver.db['requests'].update(
            {'_id': request['_id']},
            {'$set': {'inviteIds': invitesGenerated}},
            upsert=False, multi=False
        )

# on_insert_requestInvites
def requestInviteExpiry(requestInvites):
    ''' (dict) -> NoneType
    An Eve hook used to add an expiry time of 15 minutes to each
    requestInvite.
    '''

    for requestInvite in requestInvites:
        requestInvite['requestExpiry'] = datetime.utcnow() + timedelta(
            minutes=15
        )

# on_update_requestInvites
def allowAcceptanceOfRequestInvite(changes, requestInvite):
    ''' (dict) -> NoneType
    An Eve hook used to determine if a requestInvite can be accepted or not
    by its requestExpiry < currentTime.
    '''

    if (('accepted' in changes)
        and (changes['accepted'] and not requestInvite['accepted'])
    ):
        if (requestInvite['requestExpiry'] > datetime.utcnow()):

            # invite has expired, force unacceptable
            abort(422)

# on_updated_requestInvites
def alertOwnerOfAcceptedRequestInvite(changes, requestInvite):
    ''' (dict) -> NoneType
    An Eve hook used to alert the request owner of a requestInvite that was
    successfully accepted by the invitee.
    '''

    if (('accepted' in changes)
        and (changes['accepted'] and not requestInvite['accepted'])
    ):
        requestOwner = app.data.driver.db['users'].find({
            '_id': requestInvite['from']
        })

        # alert request owner of the acceptance
        gcmSend(requestOwner['deviceId'], {
            'type': 'requestInviteAccepted',
            'requestInviteAccepted': (lambda a, b: a.update(b) or a)(
                requestInvite, changes
            )
        })

# location hooks

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
