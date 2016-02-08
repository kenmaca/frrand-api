from flask import abort

def abortUnsupportedVersion():
    ''' Raised when attempting to connect with an outdated client.
    '''

    abort(403, 'Your client is out-of-date and unsupported by the API. '
        + 'Please upgrade to a newer version.')
