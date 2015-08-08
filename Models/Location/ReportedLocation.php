<?php namespace OTW\Models\Location;

// the distance (in meters) between points reportable
define('POINT_ACCURACY', 10);
define('LOCATION_KEY', 'loc');

class ReportedLocation extends \OTW\Models\MongoObject
{
    public static $mongoDataSource;

    public function __construct($json) {
        parent::__construct($json, self::$mongoDataSource);
    }

    public function update() {
        return $this->push(LOCATION_KEY);
    }

    public function incrementReportedCount() {
        $this->data['reported'][] = new \MongoDate();

        $this->update();
        return $this;
    }

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

    public static function all($username = null, $asJson = false) {
        return self::find(
            ($username ? array('username' => $username) : array()),
            $asJson
        );
    }

    public static function find($query, $asJson = false) {
        return parent::pull(self::$mongoDataSource, $query, $asJson);
    }

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
