<?php namespace OTW\Models\Location;

class TimedRoute
{
    protected $points;

    /**
     * Constructs a new TimedRoute from a bunch of ReportedLocations found 
     * either in MongoDB or another TimedRoute.
     *
     * @param MongoDate The start period of this TimedRoute
     * @param MongoDate The end period of this TimedRoute
     * @param string The username that reported this TimedRoute
     * @param TimedRoute The TimedRoute that this TimedRoute is a subset
     & of (optional)
     */
    public function __construct($startTime = null, $endTime = null,
        $username = null
    ) {
        $this->points = array();

        // build dict for points with key as date (to sort by date)
        $reportedPoints = ReportedLocation::all($username, $startTime,
            $endTime
        );

        foreach($reportedPoints as $point) {
            foreach($point->getReported() as $pointReportedTime) {

                // only add to this TimedRoute if it's within $startTime
                // and $endTime
                if ((!$startTime && !$endTime)
                    || (!$endTime
                        && $startTime
                        && ($startTime <= $pointReportedTime)
                    ) || (!startTime
                        && $endTime
                        && ($endTime > $pointReportedTime)
                    ) || (
                        $startTime <= $pointReportedTime
                        && $endTime > $pointReportedTime
                    )
                ) {
                    $this->points[
                        $pointReportedTime->toDateTime()->getTimeStamp()
                    ] = $point;
                }
            }
        }

        // finally, sort
        ksort($this->points);

        // and remove duplicate adjacent points
        $previous = null;
        $uniqueTimedRoute = array_filter(
            $this->points,
            function ($value) use (&$previous) {
                $p = $previous;
                $previous = $value;
                return $value !== $p;
            }
        );

        $this->points = $uniqueTimedRoute;
    }

    /**
     * Retrieves all points in this TimedRoute.
     *
     * @return array
     */
    public function getPoints() {
        return $this->points;
    }

    /**
     * Returns a geoJSON LineString of this TimedRoute.
     *
     * @return array
     */
    public function asLineString() {
        $linePoints = array();

        foreach($this->points as $point) {
            $linePoints[] = array(
                $point->getLong(),
                $point->getLat(),
            );
        }

        return array(
            'type' => 'LineString',
            'coordinates' => $linePoints
        );
    }
}

?>
