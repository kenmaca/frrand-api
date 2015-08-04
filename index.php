<?php

// Composer
require 'vendor/autoload.php';

// Slim API
$app = new \Slim\Slim();
$app->view(new \JsonApiView());
$app->add(new \JsonApiMiddleware());
$app->config('debug', true);

function getUsers() {
    $m = new MongoClient();
    return $m->OTW->Users;
}

// API Routing: login
$app->post('/login', function () use ($app) {

    // obtain an user with matching credentials
    require_once 'models/users/user.php';
    $users = \Users\User::pull(getUsers(), array(
        'username' => $app->request()->post('username'),
        'password' => $app->request()->post('password')
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
    $dataSource = getUsers();

    // check if user exists
    $users = \Users\User::pull($dataSource, array(
        'username' => $app->request()->post('username')
    ));

    if (empty($users)) {

        // create the new user
        require_once 'models/users/user.php';
        $user = new \Users\User($dataSource, array(
            'username' => $app->request()->post('username'),
            'password' => $app->request()->post('password')
        ));

        $user->addAddress(
            $app->request()->post('homeAddress'),
            $app->request()->post('homeCity'),
            $app->request()->post('homeRegion'),
            $app->request()->post('homeCountry'),
            $app->request()->post('homePostal'),
            $app->request()->post('homeUnit')
        );

        $user->push();
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
    require_once 'models/users/user.php';
    $app->render(200, \Users\User::pull(getUsers(), array(), true));
});

// Run
$app->run();

?>
