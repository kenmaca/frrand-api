#!/usr/bin/python3
from run import app
import datetime
with app.test_request_context():

    # prune/notify stale requests
    import models.requests
    for request in app.data.driver.db['requests'].find(
        {
            'requestedTime': {'$lt': datetime.datetime.utcnow()}
        }
    ):
        request = models.requests.Request(
            app.data.driver.db,
            models.requests.Request.collection,
            **request
        )

        # order matters here, since this is a tiered approach
        if request.isStale():
            request.set('cancel', True).requestCancellation().commit()
        elif request.isPastDue():
            request.warnStale().commit()
