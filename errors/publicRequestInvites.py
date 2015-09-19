from flask import abort

def abortUnknownRequest():
    ''' Raised when attempting to create a pre-accepted Invite for
    a PublicInvite but the Request could not be resolved. Generally
    happens if the Request was deleted manually out-of-band or just missing.
    '''

    abort(422, 'Unable to create accepted invite')

def abortDuplicateCandidate():
    ''' Raised when attempting to accept a PublicInvite when the User
    already has an outstanding Invite to this PublicInvite or they're
    already in the candidate list. Generally happens if the User
    tries to accept a PublicInvite twice (or more).
    '''

    abort(
        422,
        'User already has an Invite or is scheduled to have an Invite '
        + 'to this Request'
    )
