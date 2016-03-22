from flask import current_app as app
import errors.groups

schema = {
    'name': {
        'type': 'string',
        'unique': True,
        'required': True
    },
    'admins': {
        'type': 'list',
        'schema': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'users',
                'field': '_id'
            }
        },
        'default': []
    },
    'logo': {
        'type': 'media'
    },
    'cover': {
        'type': 'media'
    },
    'deliveries': {
        'type': 'integer',
        'default': 0,
        'readonly': True
    }
}

config = {
    'item_title': 'group',
    'public_methods': ['GET'],
    'public_item_methods': ['GET'],
    'item_methods': ['GET', 'PATCH'],
    'resource_methods': ['GET', 'POST'],
    'auth_field': None,
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_inserted_groups += onInserted
    app.on_update_groups += onUpdate

# hooks

def onInserted(groups):
    ''' (dict) -> NoneType
    An Eve hook called after insertion.
    '''

    import models.users
    user = models.users.getCurrentUser(app.data.driver.db)
    if user:
        for group in groups:
            import models.groups
            group = models.groups.Group(
                app.data.driver.db,
                models.groups.Group.collection,
                **group
            )

            if not (user.getId() in group.get('admins')):

                # add creator as an admin of newly created Group
                group.push('admins', user.getId()).commit()

def onUpdate(changes, original):
    ''' (dict, dict) -> NoneType
    An Eve hook used before update.
    '''

    import models.users
    user = models.users.getCurrentUser(app.data.driver.db)
    if not user or not (user.getId() in original['admins']):
        errors.groups.abortNotAdmin()
