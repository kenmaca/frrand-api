<?php namespace OTW\Routes\GCM;

// POST /gcm: test use for gcmSend
$app->post('/gcm', function() use ($app) {
    $user = \OTW\Models\Users\User::fromApiKey(
        $app->request()->headers('Authorization')
    );

    if ($user) {
        if ($user->gcmSend(
            (array)$app->request()->post(),
            '',
            (string)$app->request()->headers('Authorization')
        )) {
            $app->render(200, array(
                'sent' => (array)$app->request()->post(),
                'sentTo' => $user->getGcmInstanceIdFromApiKey(
                    (string)$app->request()->headers('Authorization')
                )
            ));
        } else {
            $app->render(400, array(
                'error' => true,
                'msg' => 'Associated gcmInstanceId is faulty'
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
