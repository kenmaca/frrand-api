#!/usr/local/bin/python3.4
from run import app
from eve.methods.post import post_internal
from datetime import datetime
with app.test_request_context():

    # drop collections
    for collection in app.data.driver.db.collection_names():
        if collection != 'system.indexes':
            app.data.driver.db[collection].remove({})

    # now create default user
    resp = post_internal('users', {
        'deviceId': '123',
        'phone': '123',
        'password': 'hello123'
    })

    if resp[3] == 201:
        import models.users as users
        user = users.User.fromObjectId(
            app.data.driver.db,
            resp[0]['_id']
        )

        # post a location
        resp = post_internal('locations', {
            'location': {
                'type': 'Point',
                'coordinates': [-79.302587, 43.869441]
            }
        })

        # create an apiKey
        app.data.driver.db['apiKeys'].insert(
            {
                'deviceId': '123',
                'apiKey': 'testing',
                'createdBy': user.getId()
            }
        )

        if resp[3] == 201:
            import models.locations as locations

            # set owner of location
            (
                locations.Location.fromObjectId(
                    app.data.driver.db,
                    resp[0]['_id']
                ).set('createdBy', user.getId())
                .setCurrent()
                .mergePrevious(3, 4)
                .buildTravelRegion(5)
                .commit()
            )

            # create a request
            resp = post_internal('requests', {
                'items': [{
                    'name': 'Pizza',
                    'description': 'Pepperoni and Cheese',
                    'quantity': 1,
                    'price': 9.99
                }],
                'places': [{
                    'name': 'Pizza Pizza',
                    'address': '4348 Steeles Avenue West',
                    'location': {
                        'type': 'Point',
                        'coordinates': [-79.562858, 43.766931],
                    },
                    'placeId': '100010001'
                }],
                'requestedTime': 'Tue, 02 Apr 2013 10:29:13 GMT'
            })


            if resp[3] == 201:
                import models.requests as requests
                request = requests.Request.fromObjectId(
                    app.data.driver.db,
                    resp[0]['_id']
                )

                # fill in the blanks and generate public invite
                request.set('createdBy', user.getId()).commit()
                request.getOwner().stashPoints(request.getPoints()).commit()

                import routes.requests as requestsRoute
                requestsRoute._addDefaultDestination(request)
                requestsRoute._refreshInvites(request)
                request.commit()

                print('API was reset at %s' % datetime.now())
