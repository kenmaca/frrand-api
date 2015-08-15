<?php namespace OTW\Routes\Users\Addresses;

// GET /users/addresses: lists all addresses on file for the given user
$app->get('/users/:username/addresses', function($username) use ($app) {
    $user = \OTW\Models\Users\User::authenticateApiKey(
        $app->request()->headers('Authorization'),
        $username
    );

    if ($user) {
        $app->render(200, array(
            'addresses' => $user->getAddresses()
        ));
    } else {
        $app->render(403, array(
            'error' => true,
            'msg' => 'API Key is unauthorized to access ' . $username
        ));
    }
});

?>
