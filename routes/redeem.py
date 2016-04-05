from flask import current_app as app, abort, g
import errors.redeem

schema = {
    'voucher': {
        'type': 'string',
        'minlength': 1,
        'required': True,
        'data_relation': {
            'resource': 'vouchers',
            'field': 'voucher'
        }
    }
}

config = {
    'item_title': 'redeemed',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'item_methods': [],
    'resource_methods': ['POST'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_redeem += onInsert
    app.on_inserted_redeem += onInserted

# hooks

# on_insert_redeem
def onInsert(redeems):
    ''' (list of dicts) -> NoneType
    An Eve hook used prior to insertion.
    '''

    import models.vouchers
    import models.users
    user = models.users.getCurrentUser(app.data.driver.db)
    if user:
        for redeemed in redeems:
            try:
                voucher = models.vouchers.Voucher.findOne(
                    app.data.driver.db,
                    voucher=redeemed['voucher']
                )            
                if voucher.isUsed() or not voucher.isEligible(user):
                    raise KeyError('Voucher has already been claimed')
                if not voucher.isActive():
                    raise KeyError('Voucher is not active yet or has already expired')

            except KeyError as e:
                errors.redeem.abortInvalidVoucher(str(e))
    else:
        errors.redeem.abortUnknownUser()

# on_inserted_redeem
def onInserted(redeems):
    ''' (list of dicts) -> NoneType
    An Eve hook used after insertion.
    '''

    import models.vouchers
    import models.users
    user = models.users.getCurrentUser(app.data.driver.db)
    for redeemed in redeems:
        voucher = models.vouchers.Voucher.findOne(
            app.data.driver.db,
            voucher=redeemed['voucher']
        )
        voucher.use(user).commit()
