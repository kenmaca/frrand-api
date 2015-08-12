<?php namespace OTW\Models\Location;

/**
 * A grid of ReportedLocation references (by _id) organized
 * by a 2D grid of Weekday, Hour (24) for a given User.
 */
class ReportedLocationGrid extends \OTW\Models\MongoObject
{
    // a single copy of the Collection used for all ReportedLocationGrids
    // to avoid creating multiple wasteful connections
    public static $mongoDataSource;

    /**
     * Constructs a ReportedLocationGrid.
     *
     * @param array A 1-to-1 representation of this ReportedLocationGrid
     * in MongoDB
     */
    public function __construct($json) {
        parent::__construct($json, self::$mongoDataSource);
    }

    /**
     * Updates this ReportedLocationGrid in MongoDB with any changes made.
     *
     * @return ReportedLocationGrid
     */
    public function update() {
        return $this->push(\OTW\Models\Users\USER_KEY);
    }

    /**
     * Checks if the given ReportedLocation has already been reported
     * this hour.
     *
     * @param ReportedLocation The ReportedLocation to check
     * @param MongoDate The time of reporting to check
     *
     * @return boolean
     */
    public function hasBeenReported($location, $reportTime) {
        $time = $reportTime->toDateTime();
        $dayOfWeekReported = $time->format('N');
        $hourReported = $time->format('G');
        $date = $time->format('YmdG');

        $locationsReported = $this->locationsReportedAt($dayOfWeekReported,
            $hourReported
        );

        // check if the location was registered under the grid during the 
        // given time
        if ($locationsReported) {
            if (array_key_exists($location->getObjectId(), $locationsReported)) {

                // check if the reported time was today at the same hour
                foreach($locationsReported[$location->getObjectId()]
                    as $reportedTime
                ) {
                    if ($date == $reportedTime->toDateTime()->format('YmdG')) {
                        return true;
                    }
                }
            }
        }

        return false;
    }

    /**
     * Gets the list of ReportedLocations represented by an array
     * with string:objectId => {MongoDate:reportedTime, ..} of the
     * given dayOfWeek (1-7) and hour (0-23).
     *
     * @param integer The week day
     * @param integer The hour
     *
     * @return array
     */
    public function locationsReportedAt($dayOfWeekReported, $hourReported) {
        if (array_key_exists($dayOfWeekReported, $this->data['dayOfWeek'])) {
            $day = $this->data['dayOfWeek'][$dayOfWeekReported];
            if (array_key_exists($hourReported, $day)) {
                return $day[$hourReported];
            }
        }
    }

    /**
     * Inserts a new ReportedLocation to this ReportedLocationGrid.
     * Requires that the ReportedLocation was recently updated.
     *
     * @param ReportedLocation The ReportedLocation to insert
     *
     * @return ReportedLocationGrid
     */
    public function insert($location) {
        $time = $location->getLastReported()->toDateTime();
        $dayOfWeekReported = $time->format('N');
        $hourReported = $time->format('G');

        if (!$this->hasBeenReported($location, $location->getLastReported())) {
            if (array_key_exists($dayOfWeekReported, 
                $this->data['dayOfWeek']
            )) {
                $day = $this->data['dayOfWeek'][$dayOfWeekReported];
                if (array_key_exists($hourReported, $day)) {
                    $hour = $day[$hourReported];
                    if (array_key_exists($location->getObjectId(), $hour)) {

                        // this dayOfWeek/hour/locationObjectId was
                        // previous reported, so simply add to the reported
                        // list and sort by number of reports
                        $this->data['dayOfWeek'][
                            $dayOfWeekReported
                        ][$hourReported][
                            $location->getObjectId()
                        ][] = $location->getLastReported();

                        uasort($this->data['dayOfWeek'][
                                $dayOfWeekReported
                            ][$hourReported], function ($a, $b) {
                                return (count($b) - count($a));
                            }
                        );

                    // no ReportedLocation was ever reported for this
                    // dayOfWeek/hour/locationObjectId, so init
                    } else {
                        $this->data['dayOfWeek'][
                            $dayOfWeekReported
                        ][$hourReported][
                            $location->getObjectId()
                        ] = array(
                            $location->getLastReported()
                        );
                    }

                // no ReportedLocation was ever reported for this
                // dayOfWeek/hour, so init this dayOfWeek/hour
                } else {
                    $this->data['dayOfWeek'][
                        $dayOfWeekReported
                    ][$hourReported] = array(
                        $location->getObjectId() => array(
                            $location->getLastReported()
                        )
                    );
                }

            // no ReportedLocation was ever reported for this dayOfWeek,
            // so init this dayOfWeek
            } else {
                $this->data['dayOfWeek'][$dayOfWeekReported] = array(
                    $hourReported => array(
                        $location->getObjectId() => array(
                            $location->getLastReported()
                        )
                    )
                );
            }
        }

        // finally update in MongoDB
        return $this->update();
    }

    /**
     * Gets a ReportedLocationGrid for the given $username.
     *
     * @param string The username
     *
     * @return ReportedLocationGrid
     */
    public static function get($username, $asJson = false) {
        $locationGrid = self::find(array(
            'username' => $username
        ));

        // new user, so initialized grid if the user exists
        if (!$locationGrid && \OTW\Models\Users\User::exists($username)) {
            $locationGrid = new ReportedLocationGrid(array(
                'username' => $username,
                'dayOfWeek' => array(),
            ));
            $locationGrid->update();

        // get the first one (shouldn't be any others)
        } else {
            $locationGrid = $locationGrid[0];
        }

        return $asJson ? $locationGrid->asJson() : $locationGrid;
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
}

// Initialize static instance of MongoDB connection
$mongo = new \MongoClient(\OTW\Models\MONGO_SERVER);
ReportedLocationGrid::$mongoDataSource = $mongo->OTW->LocationGrid;

?>
