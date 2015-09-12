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

        try:
            import models.apiKeys as apiKeys
            apiKey = apiKeys.APIKey.findOne(
                app.data.driver.db,
                apiKey=token
            )

            # set ownership of any resources created/modified by this user
            self.set_request_auth_value(apiKey.get('createdBy'))

            # logout any other users using this deviceId
            import models.users as users
            for user in app.data.driver.db['users'].find(
                {'deviceId': apiKey.get('deviceId')}
            ):

                # remove from user itself
                user = users.User(
                    app.data.driver.db,
                    users.User.collection,
                    **user
                ).set('deviceId', None).commit()

                # now, the actual key
                apiKey.prune()

            # set last used apiKey for this user
            users.User.fromObjectId(
                app.data.driver.db,
                apiKey.get('createdBy')
            ).useApiKey(apiKey).commit()

            return apiKey

        except KeyError:
            pass

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

        try:
            import models.users as users
            user = users.User.findOne(
                app.data.driver.db,
                username=username
            )

            # set creation of apiKey to this user
            self.set_request_auth_value(user.getId())

            # and test password
            return user.authenticate(password)

        except KeyError:
            pass

# deny all (http) requests
class NoAuth(BasicAuth):
    ''' An authentication method to block out all non-internal HTTP requests.
    '''

    def check_auth(self, username, password, allowed_roles, resource, method):
        ''' (NoAuth, str, str, list, str, str) -> bool
        Always fails authentication.
        '''

        return None
