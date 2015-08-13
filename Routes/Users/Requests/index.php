<?php namespace OTW\Routes\Users\Requests;

// POST /users/requests: adds a new reported location for the given user
$app->post('/users/:username/requests', function($username) use ($app) {
    $user = \OTW\Models\Users\User::authenticateApiKey(
        $app->request()->headers('Authorization'),
        $username
    );

    if ($user) {
        $request = \OTW\Models\Requests\Request::create(
            json_decode((string)$app->request()->post('items'), true),
            json_decode((string)$app->request()->post('places'), true),
            new \MongoDate(),
            $username
        );

        if ($request) {
            $allUsers = \OTW\Models\Users\User::all();
            foreach($allUsers as $user) {
                \OTW\Models\Requests\RequestInvitation::invite($request, $user);
            }

            $app->render(201, array());
        } else {
            $app->render(400, array(
                'error' => true,
                'msg' => 'Unable to create a new Request'
            ));
        }
    } else {
        $app->render(403, array(
            'error' => true,
            'msg' => 'API Key is unauthorized to modify ' . $username
        ));
    }
});

?>
