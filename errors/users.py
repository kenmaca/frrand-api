from flask import abort

def abortFacebookInvalidToken():
    ''' Raised when attempting to insert a Facebook Access Token that does
    not authenticate properly with Facebook.
    '''
    
    abort(422, 'Facebook Access Token is invalid')

def abortFacebookDuplicateAccount():
    ''' Raised when attempting to insert a Facebook Access Token originating
    from a Facebook user that already has another account.
    '''

    abort(422, 'Facebook account is already associated with another user')

def abortUsernameReserved():
    ''' Raised when attempting to register a reserved username.
    '''

    abort(422, 'Username is reserved')
