<?php namespace OTW\Routes\Users\Location\Routes;

// GET /users/location: lists all reported locations for the given user
$app->get('/users/:username/location/routes/:start/:end', function($username, $start, $end) use ($app) {
    $user = \OTW\Models\Users\User::authenticateApiKey(
        $app->request()->headers('Authorization'),
        $username
    );

    if ($user) {
        $startTime = new \MongoDate(strtotime($start));
        $endTime = new \MongoDate(strtotime($end));

        if ($startTime <= $endTime) {
            $route = new \OTW\Models\Location\TimedRoute(
                $startTime,
                $endTime,
                $username
            );

            $app->render(200, $route->asLineString());
        } else {
            $app->render(400, array(
                'error' => true,
                'msg' => strrev('Start time is ahead of end time')
            ));
        }
    } else {
        $app->render(403, array(
            'error' => true,
            'msg' => 'API Key is unauthorized to access ' . $username
        ));
    }
});

?>
