<?php namespace OTW\Routes\Users\Location;

// POST /users/location: adds a new reported location for the given user
$app->post('/users/:username/location', function($username) use ($app) {
    $user = \OTW\Models\Users\User::fromApiKey(
        $app->request()->headers('Authorization')
    );

    if ($user && strcmp($user->getUsername(), $username) == 0) {

        // log current location for User with $username
        $location = \OTW\Models\Location\ReportedLocation::report(
            (float)$app->request()->post('longitude'),
            (float)$app->request()->post('latitude'),
            (string)$username
        );

        $app->render(201, array());
    } else {
        $app->render(403, array(
            'error' => true,
            'msg' => 'API Key is unauthorized to modify ' . $username
        ));
    }
});

// GET /users/location: lists all reported locations for the given user
$app->get('/users/:username/location', function($username) use ($app) {
    $user = \OTW\Models\Users\User::fromApiKey(
        $app->request()->headers('Authorization')
    );

    if ($user && strcmp($user->getUsername(), $username) == 0) {
        $app->render(200, array(
            'lastReportedLocations' =>
                \OTW\Models\Location\ReportedLocation::all($username, true)
        ));
    } else {
        $app->render(403, array(
            'error' => true,
            'msg' => 'API Key is unauthorized to access ' . $username
        ));
    }
});

?>
