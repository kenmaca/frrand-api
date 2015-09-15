from flask import current_app as app, g
import gcm.comments

schema = {
    'requestId': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'requests',
            'field': '_id'
        },
        'required': True
    },
    'createdBy': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'users',
            'field': '_id'
        },
        'readonly': True
    },
    'comment': {
        'type': 'string',
        'minLength': 1,
        'maxLength': 240,
        'required': True
    }
}

config = {
    'item_title': 'comment',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': ['requestId'],
    'item_methods': ['GET'],
    'resource_methods': ['GET', 'POST'],
    'auth_field': None,
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_inserted_comments += onInserted

# on_inserted_comments
def onInserted(insertedComments):
    ''' (dict) -> NoneType
    An Eve hook used after insertion.
    '''

    for insertedComment in insertedComments:
        import models.comments as comments
        
        # set owner
        comment = comments.Comment(
            app.data.driver.db,
            comments.Comment.collection,
            **insertedComment
        ).setOwner(g.get('auth_value')).commit()

        # now message request owner
        comment.getRequest().getOwner().message(
            *gcm.comments.new(comment.getId())
        )