from flask import abort

def abortInvalidVoucher(message=None):
    ''' Raised when attempting to use an invalid (or ineligible) Voucher.
    '''

    abort(422, message or 'A ineligible or invalid Voucher was used')

def abortUnknownUser():
    ''' Raised when attempting to use a Voucher but the currently logged in User could not be resolved.
    '''

    abort(422, 'Unable to resolve the current User to apply the Voucher towards')
