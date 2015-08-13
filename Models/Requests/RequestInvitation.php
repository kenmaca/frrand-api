<?php namespace OTW\Models\Requests;

// the default amount of time a RequestInvitation expires in
define('OTW\Models\Requests\EXPIRY_TIME', '+2 minutes');

/**
 * A representation of a RequestInvitation for a Request.
 */
class RequestInvitation extends \OTW\Models\MongoObject
{
    // a single copy of the Collection used for all RequestInvitations
    // to avoid creating multiple wasteful connections
    public static $mongoDataSource;

    /**
     * Constructs a RequestInvitation..
     *
     * @param array A 1-to-1 representation of this RequestInvitation 
     * in MongoDB
     */
    public function __construct($json) {
        parent::__construct($json, self::$mongoDataSource);
    }

    /**
     * Updates this RequestInvitation in MongoDB with any changes made.
     *
     * @return Request
     */
    public function update() {
        return $this->push();
    }

    /**
     * Sends this RequestInvitation to the assigned User.
     *
     * @return boolean
     */
    public function send() {
        $user = \OTW\Models\Users\User::fromObjectId($this->data['user']);
        $request = Request::fromObjectId($this->data['request']);

        return $user->gcmSend(array(
            'type' => 'requestInvitation',
            'requestInvitation' => json_encode(array_merge(
                $request->asJson(),
                array(
                    'requesterLocation' => array(
                        'type' => 'Point',
                        'coordinates' => array(
                            0,
                            0
                        )
                    )
                )
            ))
        ));
    }

    /**
     * Finds RequestInvitations where the values of any specified
     * attributes in $query match those in MongoDB.
     *
     * @param array The query
     * @param boolean Whether to return each RequestInvitation as an array
     *
     * @return array
     */
    public static function find($query, $asJson = false) {
        return parent::pull(self::$mongoDataSource, $query, $asJson);
    }

    /**
     * Creates a new RequestInvitation.
     *
     * @param Request The RequestInvitation's Request
     * @param User The User assigned to the RequestInvitation
     *
     * @return RequestInvitation
     */
    public static function invite($request, $user) {
        $invite = new RequestInvitation(array(
            '_id' => new \MongoId(),
            'request' => $request->getObjectId(),
            'user' => $user->getObjectId(),
            'requestExpires' => new \MongoDate(strtotime(EXPIRY_TIME))
        ));

        // store in MongoDB only if the RequestInvitation was sent
        if ($invite->send()) {
            return $invite->update();
        }
    }
}

// Initialize static instance of MongoDB connection
$mongo = new \MongoClient(\OTW\Models\MONGO_SERVER);
RequestInvitation::$mongoDataSource = $mongo->OTW->RequestInvitations;

?>
