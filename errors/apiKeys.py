from flask import abort

def abortFaultyDeviceId():
    ''' Raised when attempting to create an APIKey with an non-existent
    deviceId.
    '''

    abort(401, 'Unable to create an APIKey due to a faulty deviceId being provided.')
