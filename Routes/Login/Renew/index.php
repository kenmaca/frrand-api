<?php namespace OTW\Routes\Users\Addresses;

// GET /login/renew: renews the apiKey with an updated gcmInstanceId
$app->post('/login/renew', function() use ($app) {
    $user = \OTW\Models\Users\User::fromApiKey(
        $app->request()->headers('Authorization')
    );

    if ($user) {
        if ($user->addApiKey(
            (string)$app->request()->headers('Authorization'),
            (string)$app->request()->post('gcmInstanceId')
        )) {
            $app->render(200, array());
        } else {
            $app->render(400, array(
                'error' => true,
                'msg' => 'Provided gcmInstanceId is faulty'
            ));
        }
    } else {
        $app->render(403, array(
            'error' => true,
            'msg' => 'API Key is unauthorized'
        ));
    }
});

?>
