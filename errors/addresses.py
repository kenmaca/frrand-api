from flask import abort

def abortImmutableCoordinates():
    ''' Raised when attempting to change the location of an Address.
    '''

    abort(422, 'Coordinates are read-only')

def abortUnknownAddress(message=None):
    ''' Raised when attempting to update an Address with an address that is
    not able to be geocoded.
    '''

    abort(422, message or 'Address provided is not in the right format or could not be found')

def abortAddressUniqueness():
    ''' Raised when attempting to create a new Address that already exists for
    this User. Address coordinates are rounded off to 3 decimal places (within
    111m on both latitude and longitude), so an Address that's within 111m
    on either latitude and longitude will be considered the same.
    '''

    abort(422, 'Address already exists')
