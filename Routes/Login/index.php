<?php namespace OTW\Routes\Login;

// POST /login: obtains a corresponding API key for the given user
$app->post('/login', function () use ($app) {

    // obtain an user with matching credentials
    $users = \OTW\Models\Users\User::find(array(
        'username' => (string)$app->request()->post('username'),
        'password' => (string)$app->request()->post('password')
    ));

    if (!empty($users)) {

        // generate a temporary api key and link to user
        $apiKey = \base_convert(md5(rand()), 16, 36);
        if (!$users[0]->addApiKey(
            $apiKey,
            (string)$app->request()->post('gcmInstanceId')
        )) {
            $app->render(400, array(
                'error' => true,
                'msg' => 'Provided gcmInstanceId is faulty'
            ));
        } else {
            $app->render(200, array());
        }
    } else {
        $app->render(401, array(
            'error' => true,
            'msg' => 'Authentication failed'
        ));
    }
});

?>
