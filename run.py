#!/usr/local/bin/python3.4

from eve import Eve
from eve.auth import TokenAuth, BasicAuth
from eve.methods.post import post_internal
from eve_docs import eve_docs
from gcm import GCM
from flask import abort
from flask_bootstrap import Bootstrap
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

# custom hooks
def provisionApiKey(documents):
    for document in documents:
        apiKey = (''.join(random.choice(string.ascii_uppercase) 
            for x in range(32)))

        # only insert into MongoDB if GCM went through
        try:
            response = GCM(GCM_API_KEY).json_request(
                registration_ids=[document['deviceId']],
                data={
                    'type': 'apiKey',
                    'apiKey': apiKey
                }
            )

            # gcm send failed, so skip adding to db
            if 'errors' in response:
                abort(422)

            # inject generated apiKey to doc
            document['apiKey'] = apiKey

        except Exception as e:
            abort(422)

def initNewUser(documents):
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

if __name__ == '__main__':
    app = Eve(auth=APIAuth)

    # custom hooks
    app.on_insert_apiKeys += provisionApiKey
    app.on_inserted_users += initNewUser

    # inject user:pass auth for login api provisioning
    app.config['DOMAIN']['apiKeys']['authentication'] = UserAuth

    # eve_docs addon
    Bootstrap(app)
    app.register_blueprint(eve_docs, url_prefix='/docs')

    # run
    app.run(host='0.0.0.0')
