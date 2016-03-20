from flask import abort

def abortNotAdmin():
    ''' Raised when attempting to change a Group without administrative permission.
    '''

    abort(403, 'Unable to modify Group due to insufficient administrative permissions')
