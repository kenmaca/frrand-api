<?php namespace OTW\Models\Location;

// the distance (in meters) between points reportable
define('POINT_ACCURACY', 10);
define('LOCATION_KEY', 'loc');

/**
 * A representation of a Reported Location for an User.
 */
class ReportedLocation extends \OTW\Models\MongoObject
{
    // a single copy of the Collection used for all ReportedLocations
    // to avoid creating multiple wasteful connections
    public static $mongoDataSource;

    /**
     * Constructs a ReportedLocation.
     *
     * @param array A 1-to-1 representation of this ReportedLocation in MongoDB
     */
    public function __construct($json) {
        parent::__construct($json, self::$mongoDataSource);
    }

    /**
     * Updates this ReportedLocation in MongoDB with any changes made.
     *
     * @return ReportedLocation
     */
    public function update() {
        return $this->push(LOCATION_KEY);
    }

    /**
     * Increments the times that this ReportedLocation has been reported.
     *
     * @return ReportedLocation
     */
    public function incrementReportedCount() {
        $this->data['reported'][] = new \MongoDate();
        return $this->update();
    }

    /**
     * Finds any previously ReportedLocations for the given User with
     * $username is within POINT_ACCURACY meters away from the given
     * $longitude and $latitude.
     *
     * @param float The longitude of a given point
     * @param float The latitude of a given point
     * @param string The username to look for or null to search all
     * ReportedLocations in MongoDB
     *
     * @return array
     */
    public static function near($longitude, $latitude, $username = null) {
        $query = array(
            'loc' => array(
                '$near' => array(
                    '$geometry' => array(
                        'type' => 'Point',
                        'coordinates' => array($longitude, $latitude)
                    ),
                    '$maxDistance' => POINT_ACCURACY
                )
            )
        );

        if ($username) $query['username'] = $username;
        return self::find($query);
    }

    /**
     * Gets all ReportedLocations for a given User with $username.
     *
     * @param string The username
     * @param boolean Whether to return each ReportedLocation as an array
     *
     * @return array
     */
    public static function all($username = null, $asJson = false) {
        return self::find(
            ($username ? array('username' => $username) : array()),
            $asJson
        );
    }

    /**
     * Finds ReportedLocations where the values of any specified
     * attributes in $query match those in MongoDB.
     *
     * @param array The query
     * @param boolean Whether to return each ReportedLocation as an array
     *
     * @return array
     */
    public static function find($query, $asJson = false) {
        return parent::pull(self::$mongoDataSource, $query, $asJson);
    }

    /**
     * Creates a new ReportedLocation if there isn't any previous existing
     * ReportedLocation that is near the given $longitude and $latitude for
     * the given User with $username within POINT_ACCURACY -- otherwise
     * update the matching near ReportedLocation with a reported timestamp
     * to indicate that the ReportedLocation was reported again.
     *
     * @param float The longitude
     * @param float The latitude
     * @param string The username
     *
     * @return ReportedLocation
     */
    public static function report($longitude, $latitude, $username) {
        $location = self::near($longitude, $latitude, $username);

        // found location within POINT_ACCURACY meters away in history
        if ($location) {
            $location = $location[0];
            $location->incrementReportedCount();

        // never been reported, so create new Location
        } else {

            // only log Location if the user exists
            if (\OTW\Models\Users\User::exists($username)) {
                $location = new ReportedLocation(array(
                    'username' => $username,
                    'reported' => array(new \MongoDate()),
                    'loc' => array(
                        'type' => 'Point',
                        'coordinates' => array($longitude, $latitude)
                    ),
                    'created' => new \MongoDate()
                ));

                $location->update();
            }
        }

        return $location;
    }
}

// Initialize static instance of MongoDB connection
$mongo = new \MongoClient(\OTW\Models\MONGO_SERVER);
ReportedLocation::$mongoDataSource = $mongo->OTW->Location;

?>
