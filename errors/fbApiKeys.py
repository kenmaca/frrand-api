from flask import abort

def abortInvalidFacebookToken():
    ''' Raised when attempting to create an APIKey with a Facebook token that
    failed to authenticate.
    '''

    abort(401, 'Provided Facebook Token failed to authenticate.')
