<?php namespace OTW\Routes\Users\Location;

// GET /users/location/grid: shows the reported location frequency grid
$app->get('/users/:username/location/grid', function($username) use ($app) {
    $user = \OTW\Models\Users\User::authenticateApiKey(
        $app->request()->headers('Authorization'),
        $username
    );

    if ($user) {
        $app->render(200, \OTW\Models\Location\ReportedLocationGrid::get(
            $username, true
        ));
    } else {
        $app->render(403, array(
            'error' => true,
            'msg' => 'API Key is unauthorized to access ' . $username
        ));
    }
});

?>
