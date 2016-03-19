from flask import abort

def abortFaultyDeviceId():
    ''' Raised when attempting to create an APIKey with an non-existent
    deviceId.
    '''

    abort(401, 'Unable to create an APIKey due to a faulty deviceId being provided.')

def abortInvalidVoucher():
    ''' Raised when attempting to create an APIKey with an invalid Voucher on an User that
    has never been activated before.
    '''

    abort(403, 'Unable to create an APIKey due to invalid Voucher.')
