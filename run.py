from eve import Eve
from eve.auth import TokenAuth
import random
import string

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

        with open('test', 'w') as fp:
            fp.write(resource)

        apiKey = app.data.driver.db['apiKeys'].find_one({'apiKey': token})
        if (apiKey and 'userId' in apiKey):
            self.set_request_auth_value(apiKey['userId'])

        return apiKey

# custom hooks
def generateApiKey(document):
    apiKey = (''.join(random.choice(string.ascii_uppercase) for x in range(16)))

    app.data.driver.db['apiKeys'].insert({
        'apiKey': apiKey,
        'deviceId': document['deviceId'],
        'userId': document['_id']
    })

def initNewUsers(documents):
    for document in documents:

        # set newly created user as self-owning
        app.data.driver.db['users'].update({
            '_id': document['_id']
        }, {
            '$set': {
                'createdBy': document['_id']
            }
        }, upsert=False, multi=False)

        # and finally, create a new apiKey
        generateApiKey(document)

if __name__ == '__main__':
    app = Eve(auth=APIAuth)
    app.on_inserted_users += initNewUsers
    app.run(host='0.0.0.0')
