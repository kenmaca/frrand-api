import models.orm as orm
from datetime import datetime
from pymongo import DESCENDING
from shapely.geometry import mapping, shape

class Location(orm.MongoORM):
    ''' A representation of a Location in Frrand.
    '''

    collection = 'locations'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Location
        Creates a Location directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, Location)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database, bson.ObjectId) -> Location
        Creates a Location directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.findOne(db, Location, **query)

    def setCurrent(self):
        ''' (Location) -> Location
        Sets this location as current and previously reported locations
        as not.
        '''

        if self.exists('createdBy'):
            self.source.update(
                {
                    'createdBy': self.get('createdBy'),
                    'current': True
                },
                {'$set': {'current': False}},
                upsert=False, multi=True
            )

        self.set('current', True)
        return self

    def getGeo(self):
        ''' (Location) -> dict
        Gets a GeoJson representation of this Location.
        '''

        return self.get('location')

    def supplementCurrentTime(self):
        ''' (Location) -> Location
        Adds dayOfWeek and hour to this location.
        '''

        self.set('dayOfWeek', datetime.utcnow().isoweekday())
        self.set('hour', datetime.utcnow().hour)
        return self

    def approximate(self, accuracy):
        ''' (Location, int) -> Location
        Rounds down the coordinates of this Location to accuracy points of
        accuracy.
        '''

        geoJson = self.get('location')
        geoJson['coordinates'] = [round(point, accuracy)
            for point in geoJson['coordinates']]
        self.set('location', geoJson)
        return self

    def mergePrevious(self, threshold, accuracy):
        ''' (Location, int, int) -> Location
        Converts a regular reported location to a stationary
        one if the location was reported threshold times in a row,
        or increments the timesReported if there is currently already a 
        stationary location for these coordinates.
        '''

        # prepare this Location just in case
        self.approximate(accuracy).commit()
        if not self.exists('dayOfWeek') or not self.exists('hour'):
            self.supplementCurrentTime()

        try:

            # check if there is already a stationary location for these
            # coordinates
            stationary = Location.findOne(
                self.db,
                hour=self.get('hour'),
                dayOfWeek=self.get('dayOfWeek'),
                location=self.get('location'),
                timesReported={'$gt': 1},
                createdBy=self.get('createdBy')
            )

            # merge with stationary and remove older location
            self.increment('timesReported', stationary.get('timesReported'))
            stationary.remove()

        except KeyError:

            # never stationary, so check if it is now
            lastReportedLocations = self.source.find(
                {'createdBy': self.get('createdBy')}
            ).sort('_id', DESCENDING).limit(threshold)

            timesReported = 0
            if lastReportedLocations:
                for lastReported in lastReportedLocations:

                    # approximate the last location (since the last one
                    # is actually this one, but not approximated)
                    lastReported = Location(
                        self.db,
                        Location.collection,
                        **lastReported
                    )

                    if lastReported.get('location') == self.get('location'):
                        timesReported += lastReported.get('timesReported')
                    else:

                        # exit prematurely if the chain is broken
                        break

            # if stationary, then merge all previous locations from this
            # timeblock cell with the same coordinates
            if timesReported >= threshold:
                locationsToMerge = self.source.find(
                    {
                        'hour': self.get('hour'),
                        'dayOfWeek': self.get('dayOfWeek'),
                        'location': self.get('location'),
                        'createdBy': self.get('createdBy')
                    }
                )

                # merge timesReported with this location and remove older doc
                if locationsToMerge:
                    for merge in locationsToMerge:
                        merge = Location(
                            self.db,
                            Location.collection,
                            **merge
                        )
                        self.increment(
                            'timesReported',
                            merge.get('timesReported')
                        )
                        merge.remove()

        return self

    def buildTravelRegion(self, limitRegion):
        ''' (Location, int) -> Location
        Creates a convex hull of this Location, the owner's permanent 
        addresses, and any frequently visited locations (more than one visit 
        concurrently) -- which represents likely places the owner will visit in
        the next two hours.

        REQ: mergePrevious was run previously
        '''

        import models.users as users
        owner = users.User.fromObjectId(self.db, self.get('createdBy'))

        # start with current location
        points = [self.get('location')['coordinates']]

        # next on priority is known addresses
        points += [address.get('location')['coordinates'] for address in 
            owner.getAddresses()
        ]
        
        # then, frequent locations reported this hour and next
        points += [reportedLocation['location']['coordinates'] for 
            reportedLocation in self.source.find(
                {'createdBy': self.get('createdBy'),
                    'hour': {'$in': [
                        self.get('hour'),
                        (self.get('hour') + 1) % 24,
                    ]},
                    'dayOfWeek': {'$in': [
                        self.get('dayOfWeek'),
                        (self.get('dayOfWeek') + 1) if (
                            (self.get('hour') + 1) % 24
                        ) else self.get('dayOfWeek')
                    ]}
                }
            ).sort('timesReported', DESCENDING)
        ][:limitRegion]

        # limit number of points to LIMIT_REGION and take the convex hull
        self.set(
            'region',
            mapping(shape(
                {'type': 'MultiPoint', 'coordinates': points}
            ).convex_hull)
        )

        return self

    def getOwner(self):
        ''' (Location) -> models.users.User
        Gets the owner of this Location.
        '''

        import models.users as users
        return users.User.fromObjectId(
            self.db,
            self.get('createdBy')
        )
