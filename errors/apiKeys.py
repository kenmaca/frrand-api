from flask import abort

def abortFaultyDeviceId():
    ''' Raised when attempting to create an APIKey with an non-existent
    deviceId.
    '''

    abort(422, 'Unable to create accepted invite')