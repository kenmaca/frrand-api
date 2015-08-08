<?php namespace OTW\Routes\Users\Addresses;

// GET /users/addresses: lists all addresses on file for the given user
$app->get('/users/:username/addresses', function($username) use ($app) {
    $user = \OTW\Models\Users\User::fromApiKey(
        $app->request()->headers('Authorization')
    );

    if ($user && strcmp($user[0]->getUsername(), $username) == 0) {
        $app->render(200, array(
            'addresses' => $user[0]->getAddresses()
        ));
    } else {
        $app->render(403, array(
            'error' => true,
            'msg' => 'API Key is unauthorized to access ' . $username
        ));
    }
});

?>
