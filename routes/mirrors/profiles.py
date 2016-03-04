from flask import current_app as app

config = {
    'item_title': 'profile',
    'public_methods': ['GET'],
    'public_item_methods': ['GET'],
    'datasource': {
        'source': 'users',
        'projection': {
            'deviceId': 0,
            'password': 0,
            'salt': 0,
            '_verificationCode': 0,
            'facebookAccessToken': 0,
            'googleAccessToken': 0,
            'verifcationCode': 0
        }
    },
    'allowed_filters': [],
    'item_methods': ['GET'],
    'resource_methods': ['GET']
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_fetched_resource_profiles += onFetched
    app.on_fetched_item_profiles += onFetchedItem

def onFetched(fetchedProfiles):
    ''' (dict) -> NoneType
    An Eve hook used after fetching profiles.
    '''

    # embed images in each request (until #719 in Eve is fixed)
    if '_items' in fetchedProfiles:
        for profile in fetchedProfiles['_items']:
            onFetchedItem(profile)

def onFetchedItem(fetchedProfile):
    ''' (dict) -> NoneType
    An Eve hook used after fetching a single profile.
    '''

    # embed images in profile (until #719 in Eve is fixed)
    if 'picture' in fetchedProfile:

        # now embed
        fetchedProfile['picture'] = '%s/%s/%s' % (
            app.config['MEDIA_BASE_URL']
                if app.config['MEDIA_BASE_URL']
                else app.api_prefix,
            app.config['MEDIA_ENDPOINT'],
            fetchedProfile['picture']
        )
