from eve.auth import TokenAuth, BasicAuth
from flask import current_app as app

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
