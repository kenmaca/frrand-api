from flask import abort
import errors.requests

def abortInviteExpired():
    ''' Raised when attempting to access an Invite that was recently expired
    and pruned.
    '''

    abort(404, 'Invite is expired')

def abortImmutableAccepted():
    ''' Raised when attempting to change the accepted status of an Invite
    that's already accepted.
    '''

    abort(
        422,
        'Cannot change accepted status of an accepted invite; '
        + 'delete Invite if refusing'
    )

def abortImmutableMutuallyCancelled():
    ''' Raised when attempting to modify a mutually cancelled Request.
    '''

    errors.requests.abortImmutableMutuallyCancelled()

def abortFeedbackUncompleted():
    ''' Raised when attempting to submit Feedback for a Request that's
    incomplete.
    '''

    errors.requests.abortFeedbackUncompleted()

def abortImmutableFeedback():
    ''' Raised when attempting to modify Feedback (which cannot be changed
    after submission).
    '''

    errors.requests.abortImmutableFeedback()

def abortDeleteAttached():
    ''' Raised when attempting to delete an attached Invite.
    '''

    abort(422, 'Cannot delete attached invite')
