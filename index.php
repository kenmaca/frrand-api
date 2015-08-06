<?php

// Dependancies
require 'vendor/autoload.php';
spl_autoload_register(function ($className) {
    $classFile = str_replace(array('OTW\\', '\\'), array('', '/'),
        $className) . '.php';

    if (file_exists($classFile)) {
        require_once $classFile;
        if (class_exists($className)) {
            return true;
        }
    }
    return false;
});

// Slim API
$app = new \Slim\Slim();
$app->view(new \JsonApiView());
$app->add(new \JsonApiMiddleware());
$app->config('debug', true);

// API Routing: login
$app->post('/login', function () use ($app) {

    // obtain an user with matching credentials
    $users = \OTW\Models\Users\User::find(array(
        'username' => (string)$app->request()->post('username'),
        'password' => (string)$app->request()->post('password')
    ));

    if (!empty($users)) {

        // generate a temporary api key and link to user
        $apiKey = \base_convert(md5(rand()), 16, 36);
        $apiExpiry = date('r');
        $users[0]->addApiKey($apiKey, $apiExpiry);
        
        $app->render(200, array(
            'apiToken' => $apiKey,
            'apiExpiry' => $apiExpiry
        ));
    } else {
        $app->render(401, array(
            'error' => true,
            'msg' => 'Authentication failed'
        ));
    }
});

// API Routing: register
$app->post('/users', function() use ($app) {
    $user = \OTW\Models\Users\User::register(
        (string)$app->request()->post('username'),
        (string)$app->request()->post('password')
    );

    if ($user) {
        $user->addAddress(
            (string)$app->request()->post('homeAddress'),
            (string)$app->request()->post('homeCity'),
            (string)$app->request()->post('homeRegion'),
            (string)$app->request()->post('homeCountry'),
            (string)$app->request()->post('homePostal'),
            (string)$app->request()->post('homeUnit')
        );

        $user->update();
        $app->render(201, array());
    } else {
        $app->render(409, array(
            'error' => true,
            'msg' => 'User already exists'
        ));
    }
});

// API Routing: list all users
// TODO: Block access, only used for debugging
$app->get('/users', function() use ($app) {
    $app->render(200, array(
        'users' => \OTW\Models\Users\User::all(true)
    ));
});

// API Routing: location report
$app->post('/users/:username/location', function($username) use ($app) {
    $user = \OTW\Models\Users\User::fromApiKey(
        $app->request()->headers('Authorization')
    );

    if ($user && strcmp($user[0]->getUsername(), $username) == 0) {
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

// API Routing: get last locations
$app->get('/users/:username/location', function($username) use ($app) {
    $user = \OTW\Models\Users\User::fromApiKey(
        $app->request()->headers('Authorization')
    );

    if ($user && strcmp($user[0]->getUsername(), $username) == 0) {
        $app->render(200, array(
            'lastReportedLocations' => 
                \OTW\Models\Location\ReportedLocation::all($username)
        ));
    } else {
        $app->render(403, array(
            'error' => true,
            'msg' => 'API Key is unauthorized to access ' . $username
        ));
    }
});

// Run
$app->run();

?>
