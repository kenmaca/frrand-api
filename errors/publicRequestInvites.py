from flask import abort

def abortUnknownRequest():
    ''' Raised when attempting to create a pre-accepted Invite for
    a PublicInvite but the Request could not be resolved. Generally
    happens if the Request was deleted manually out-of-band or just missing.
    '''

    abort(422, 'Unable to create accepted invite')