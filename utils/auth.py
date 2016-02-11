from eve.auth import TokenAuth, BasicAuth
from flask import current_app as app
from errors.general import abortUnsupportedVersion

MIN_CLIENT_VERSION = 0.01

# default authentication method
class APIAuth(BasicAuth):
    ''' An authentication method using apiKeys allowing only access
    to self-created resources.
    '''

    def check_auth(self, version, token, allowed_roles, resource, method):
        ''' (APIAuth, str, str, list, str, str) -> bool
        Checks if the provided token is a valid apiKey and has access
        to the requested resource. Also blocks version lower than
        MIN_CLIENT_VERSION.
        '''

        # refuse connection if version is too old or does not conform to
        # protocol
        try:
            if float(version[1:]) < MIN_CLIENT_VERSION:
                abortUnsupportedVersion()
        except ValueError:
            abortUnsupportedVersion()

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

# generate apiKey facebookId authentication method
class FacebookAuth(BasicAuth):
    ''' An authentication method using a FacebookId allowing only access
    to self-created resources.
    '''

    def check_auth(self, version, token, allowed_roles, resource, method):
        ''' (FacebookAuth, str, str, list, str, str) -> bool
        Checks if the provided token is a currently known FacebookId and has access
        to the requested resource.
        '''

        import models.users as users
        user = users.User.findOne(
            app.data.driver.db,
            facebookId=token
        )

        # set creation of apiKey to this user
        self.set_request_auth_value(user.getId())
        return user

# generate apiKey user:pass authentication method
class UserAuth(BasicAuth):
    ''' An authentication method using an username and password. Generally 
    used to generate an apiKey.
    '''

    def check_auth(self, username, password, allowed_roles, resource, method):
        ''' (UserAuth, str, str, list, str, str) -> bool
        Checks if the provided username and password exist as a pair in the
        database.
        '''

        try:

            # special phone login method with verification code
            if username[:6] == '_phone':

                # strip type indicator
                username = username[6:]
                import models.users as users
                user = users.User.findOne(
                    app.data.driver.db,
                    phone=username
                )

                # authenticate via verificiationCode
                if user.get('_verificationCode') == password:

                    # also serves as an verification method
                    user.set(
                        'verificationCode',
                        password
                    ).verifyPhone().commit()

                    # set creation of apiKey to this user
                    self.set_request_auth_value(user.getId())
                    return user

                # reset verificationCode if wrong
                else:
                    user.setVerificationCode().commit()


            # otherwise, fall back to standard user/pass auth
            else:
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
