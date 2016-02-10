from flask import abort

def abortExpiredInvite():
    ''' Raised when attempting to use an expired or nonexistent invite.
    '''

    abort(422, 'Invite does not exist or has expired.')

def abortImmutablePoints():
    ''' Raised when attempting to change points awarded after a
    Request has been created.
    '''

    abort(422, 'Awarded points on completion cannot be changed')

def abortImmutableInvitesOnAttached():
    ''' Raised when attempting to change invites once a Request has already
    been attached to an invite.
    '''

    abort(422, 'Cannot change Invites once attached')

def abortAlreadyAttached():
    ''' Raised when attempting to attach an invite on a Request that's
    already attached.
    '''

    abort(422, 'Already attached')

def abortAttachInvite():
    ''' Raised when attempting to attach an invite that does not exist in
    the database. Generally happens when the invite has expired before
    attach.
    '''

    abort(422, 'Unable to attach Invite')

def abortComplete():
    ''' Raised when attempting to mark a Request complete that's already
    complete.
    '''

    abort(422, 'Already complete')

def abortCompleteUnattached():
    ''' Raised when attempting to mark a Request complete that hasn't been
    attached to an Invite yet.
    '''

    abort(422, 'Cannot complete an unattached Request')

def abortFeedbackUncompleted():
    ''' Raised when attempting to submit Feedback for a Request that's
    incomplete.
    '''

    abort(422, 'Cannot submit feedback for uncompleted Request')

def abortImmutableFeedback():
    ''' Raised when attempting to modify Feedback (which cannot be changed
    after submission).
    '''

    abort(422, 'Cannot alter existing feedback')

def abortCompleteCreation():
    ''' Raised when attempting to create a new Request that's complete.
    '''

    abort(422, 'Cannot set completion on Request creation')
