#!/usr/local/bin/python3.4

from eve import Eve
from eve.auth import TokenAuth, BasicAuth
from eve.methods.post import post_internal
from eve_docs import eve_docs
from gcm import GCM
from flask import abort
from flask_bootstrap import Bootstrap
from datetime import datetime
import random
import string

# settings
GCM_API_KEY = 'AIzaSyCvJlZQUf1fEEi0812f_-yNQptbra9IRts'

# default authentication method
class APIAuth(TokenAuth):
    ''' An authentication method using apiKeys allowing only access
    to self-created resources.
    '''

    def check_auth(self, token, allowed_roles, resource, method):
        ''' (APIAuth, str, list, str, str) -> bool
        Checks if the provided token is a valid apiKey and has access
        to the requested resource.
        '''

        apiKey = app.data.driver.db['apiKeys'].find_one({'apiKey': token})
        if (apiKey and 'createdBy' in apiKey):
            self.set_request_auth_value(apiKey['createdBy'])

        return apiKey

# generate apiKey user:pass authentication method
class UserAuth(BasicAuth):
    ''' An authentication method using an username and password to
    generally used to generate an apiKey.
    '''

    def check_auth(self, username, password, allowed_roles, resource, method):
        ''' (UserAuth, str, str, list, str, str) -> bool
        Checks if the provided username and password exist as a pair in the
        database.
        '''

        user = app.data.driver.db['users'].find_one({
            'username': username,
            'password': password
        })
        if (user and '_id' in user):
            self.set_request_auth_value(user['_id'])

        return user

# deny all (http) requests
class NoAuth(BasicAuth):
    ''' An authentication method to block out all non-internal HTTP requests.
    '''

    def check_auth(self, username, password, allowed_roles, resource, method):
        ''' (NoAuth, str, str, list, str, str) -> bool
        Always fails authentication.
        '''

        return None

# communication interfaces
def gcmSend(deviceId, data):
    ''' (list of str, dict) -> bool
    Sends data via GCM to the provided deviceId and returns True
    if it worked.
    '''

    try:
        if ('errors' in GCM(GCM_API_KEY).json_request(
            registration_ids=[deviceId], data=data)
        ):
            return False
        return True

    except Exception:
        return False

# custom hooks
def provisionApiKey(documents):
    ''' (dict) -> NoneType
    An Eve hook used to generate an apiKey from a document that is about
    to be inserted containing a deviceId.

    REQ: documents was inserted via an Authenticated route,
    dependant on the createdBy auth_field
    '''

    for document in documents:
        apiKey = (''.join(random.choice(string.ascii_uppercase) 
            for x in range(32)))

        # only insert into MongoDB if GCM went through
        if (gcmSend(document['deviceId'], {
            'type': 'apiKey',
            'apiKey': apiKey
        })): 

            # inject generated apiKey to doc
            document['apiKey'] = apiKey
        else:
            abort(422)

def initNewUser(documents):
    ''' (dict) -> NoneType
    An Eve hook used to set the createdBy field for an newly
    inserted user document to itself (since Eve handles
    auth_field only when inserting via Authenticated routes).
    '''

    for document in documents:

        # set newly created user as self-owning
        app.data.driver.db['users'].update({
            '_id': document['_id']
        }, {
            '$set': {
                'createdBy': document['_id']
            }
        }, upsert=False, multi=False)

        # and finally, create a new apiKey and self-owning
        with app.test_request_context():
            post_internal('apiKeys', {
                'deviceId': document['deviceId'],
                'createdBy': document['_id']
            })

def generateRequestInvites(documents):
    ''' (dict) -> NoneType
    An Eve hook used to automatically generate RequestInvites for
    the given Requests and sends out the RequestInvite via GCM.
    '''

    # currently just sends out to ALL users (for dev use only)
    # TODO: perform candidate matching here
    users = app.data.driver.db['users'].find({})
    for document in documents:
        for user in users:
            with app.test_request_context():
                post_internal('requestInvites', {
                    'requestId': document['_id'],
                    'location': {
                        'type': 'Point',
                        'coordinates': [0.0, 0.0]
                    },
                    'from': document['createdBy'],
                    'createdBy': user['_id']
                })

def requestInviteSendGcm(documents):
    ''' (dict) -> NoneType
    An Eve hook used to send out requestInvites via GCM.
    '''

    for document in documents:
        deviceIds = app.data.driver.db['apiKeys'].find({
            'createdBy': document['createdBy']
        }).sort('_id', -1).limit(1)

        for deviceId in deviceIds:
            gcmSend(deviceId['deviceId'], {
                'type': 'requestInvite',
                'requestInvite': document
            })

def supplementLocationData(documents):
    ''' (dict) -> NoneType
    An Eve hook used to add dayOfWeek and hour data as well as
    approximate longitude and latitude within 11 metres.
    '''

    for document in documents:

        # location grid datetime injection if not provided
        if 'dayOfWeek' not in document:
            document['dayOfWeek'] = datetime.now().isoweekday()
        if 'hour' not in document:
            document['hour'] = datetime.now().hour

        # approximate coordinates
        document['location']['coordinates'] = [round(point, 4)
            for point in document['location']['coordinates']]

if __name__ == '__main__':
    app = Eve(auth=APIAuth)

    # custom hooks
    app.on_insert_apiKeys += provisionApiKey
    app.on_inserted_users += initNewUser
    app.on_inserted_requests += generateRequestInvites
    app.on_inserted_requestInvites += requestInviteSendGcm
    app.on_insert_locations += supplementLocationData

    # inject user:pass auth for login api provisioning
    app.config['DOMAIN']['apiKeys']['authentication'] = UserAuth
    app.config['DOMAIN']['requestInvites']['authentication'] = NoAuth

    # eve_docs addon
    Bootstrap(app)
    app.register_blueprint(eve_docs, url_prefix='/docs')

    # run
    app.run(host='0.0.0.0')
