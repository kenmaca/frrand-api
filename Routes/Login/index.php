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
        $users[0]->addApiKey(
            $apiKey,
            $app->request()->post('gcmInstanceId')
                ? (string)$app->request()->post('gcmInstanceId') : null
        );

        // send apiKey via GCM or JSON if gcmSend failed
        if (!$users[0]->gcmSend(
            array('apiToken' => $apiKey),
            '',
            $apiKey

        // if gcmSend failed.. fallback to JSON (need to remove)
        )) {
            $app->render(200, array(
                'apiToken' => $apiKey,
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
