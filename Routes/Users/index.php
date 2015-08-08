<?php namespace OTW\Routes\Users;

// POST /users: register new account
$app->post('/users', function() use ($app) {
    $user = \OTW\Models\Users\User::register(
        (string)$app->request()->post('username'),
        (string)$app->request()->post('password')
    );

    if ($user) {
        $user->addAddress(
            'home',
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

// GET /users: list all user accounts
// TODO: Block access, only used for debugging
$app->get('/users', function() use ($app) {
    $app->render(200, array(
        'users' => \OTW\Models\Users\User::all(true)
    ));
});

?>
