<?php namespace OTW\Models\Users;

// the designated user field to mark as an unique identifier
define('OTW\Models\Users\USER_KEY', 'username');

/**
 * A representation of an User.
 */
class User extends \OTW\Models\MongoObject implements GCMSender
{

    // a single copy of the Collection used for all Users
    // to avoid creating multiple wasteful connections
    public static $mongoDataSource;
    public static $gcmSenderService;

    /**
     * Constructs an User.
     *
     * @param array A 1-to-1 representation of this User in MongoDB
     */
    public function __construct($json) {
        parent::__construct($json, self::$mongoDataSource);
    }

    /**
     * Returns a string representation of this User.
     *
     * @return string
     */
    public function __toString() {
        return '{' . USER_KEY . ': ' . $this->data[USER_KEY] . '}';
    }

    /**
     * Obtains the username for this User.
     *
     * @return string
     */
    public function getUsername() {
        return $this->data[USER_KEY];
    }

    /**
     * Updates this User in MongoDB with any changes made.
     *
     * @return User
     */
    public function update() {
        return $this->push(USER_KEY);
    }

    /**
     * Obtains all addresses for this User.
     *
     * @return array
     */
    public function getAddresses() {
        return $this->data['addresses'];
    }

    /**
     * Records an address for this User's $name location.
     *
     * @param string An unique name for this address
     * @param string The full street
     * @param string The city
     * @param string The region
     * @param string The country
     * @param string The postal or zip code
     * @param string The unit number
     *
     * @return User
     */
    public function addAddress($name, $street, $city, $region, $country, 
        $postal, $unit = null
    ) {
        if (!\array_key_exists('addresses', $this->data)) {
            $this->data['addresses'] = array();
        }

        $this->data['addresses'][$name] = array(
            'street' => $street,
            'city' => $city,
            'region' => $region,
            'country' => $country,
            'postal' => $postal,
            'unit' => $unit,
            'created' => new \MongoDate(),
            'updated' => new \MongoDate()
        );

        return $this->update();
    }

    /**
     * Gets the most recent gcmInstanceId for this User.
     *
     * @return string
     */
    public function getLastGcmInstanceId() {
        reset($this->data['apiKeys']);
        return $this->getGcmInstanceIdFromApiKey(key($this->data['apiKeys']));
    }

    /**
     * Gets the gcmInstanceId associated with the given apiKey.
     *
     * @param string The API key
     *
     * @return string
     */
    public function getGcmInstanceIdFromApiKey($apiKey) {
        return $this->data['apiKeys'][$apiKey]['gcmInstanceId'];
    }

    /**
     * Sets a new API key for this User.
     *
     * @param string The API key
     * @param string The InstanceID from the Device requesting API access
     *
     * @return User
     */
    public function addApiKey($apiKey, $gcmInstanceId = null) {
        $this->data['apiKeys'][$apiKey] = array(
            'created' => new \MongoDate(),
            'lastUsed' => new \MongoDate(),
            'gcmInstanceId' => $gcmInstanceId
        );

        $this->pruneApiKeys();
        return $this->useApiKey($apiKey);
    }

    /**
     * Prunes the API Key array for older duplicate keys and maintains
     * a unique apiKey-to-gcmInstanceId pairing.
     *
     * @return User
     */
    public function pruneApiKeys() {

        // instanceId => apiKey
        $instanceIds = array();

        foreach($this->data['apiKeys'] as $apiKey => $keyData) {
            if (array_key_exists($keyData['gcmInstanceId'], $instanceIds)) {
                if ($keyData['created'] > $this->data['apiKeys'][
                    $instanceIds[$keyData['gcmInstanceId']]
                ]['created']) {

                    // instanceId was seen already, remove older one
                    unset($this->data['apiKeys'][
                        $instanceIds[$keyData['gcmInstanceId']]
                    ]);
                    $instanceIds[$keyData['gcmInstanceId']] = $apiKey;
                } else {

                    // current instanceId is old, so remove it
                    unset($this->data['apiKeys'][$apiKey]);
                }
            } else {

                // never tracked, so good to go
                $instanceIds[$keyData['gcmInstanceId']] = $apiKey;
            }
        }
        return $this->update();
    }

    /**
     * Updates an API Key with the time it was last used and pushes the
     * select $apiKey to the front (maintaining frequently accessed keys
     * appearing at the front of the array).
     *
     * @return User
     */
    public function useApiKey($apiKey) {

        // update lastUsed
        $apiKeyObject = $this->data['apiKeys'][$apiKey];
        $apiKeyObject['lastUsed'] = new \MongoDate();

        // push to front
        $this->data['apiKeys'] = (array($apiKey => $apiKeyObject)
            + $this->data['apiKeys']
        );

        return $this->update();
    }

    /**
     * Obtains a corresponding User from the provided API key from
     * MongoDB.
     *
     * @param string The API key
     *
     * @return User
     */
    public static function fromApiKey($apiKey) {
        $user = self::find(array(
            'apiKeys.' . $apiKey => array(
                '$exists' => true
            )
        ));

        // update lastUsed
        if ($user) return $user[0]->useApiKey($apiKey);
    }

    /**
     * Authenticates an API key with an username.
     *
     * @param string The API key
     * @param string The username
     *
     * @return User
     */
    public static function authenticateApiKey($apiKey, $username) {
        $user = self::fromApiKey($apiKey);
        if ($user) {

            // check if $apiKey matches with $username
            return (strcmp($user->getUsername(), $username) == 0)
                ? $user : null;
        }
    }

    /**
     * Sends a message to this User's last known device, returns
     * true if it was successful, and false otherwise.
     *
     * @param array The message payload
     *
     * @return bool
     */
    public function gcmSend($payload, $collapseKey = '', $apiKey = null) {
        $gcmInstanceId = ($apiKey
            ? $this->getGcmInstanceIdFromApiKey($apiKey)
            : $this->getLastGcmInstanceId()
        );

        $message = new \PHP_GCM\Message($collapseKey, $payload);

        try {
            $result = self::$gcmSenderService->send($message, $gcmInstanceId, 3);
            return $result->getErrorCode() ? false : true;
        } catch(\Exception $e) {
            return false;
        }
    }

    /**
     * Obtains a corresponding User from the provided username from
     * MongoDB.
     *
     * @param string The username
     *
     * @return User
     */
    public static function exists($username) {
        $user = self::find(array('username' => $username));
        return $user[0];
    }

    /**
     * Obtains all Users in MongoDB.
     *
     * @param boolean Whether to return each User as an array
     *
     * @return array
     */
    public static function all($asJson = false) {
        return self::find(array(), $asJson);
    }

    /**
     * Finds an User with attributes matching the $query array.
     *
     * @param array The query array to search with
     * @param boolean Whether to return each User as an array
     *
     * @return array
     */
    public static function find($query, $asJson = false) {
        return parent::pull(self::$mongoDataSource, $query, $asJson);
    }

    /**
     * Registers a new User if the username does not exist.
     *
     * @param string $username The requested username.
     * @param string $password A encrypted password.
     *
     * @return User
     */
    public static function register($username, $password) {
        if (!self::exists($username)) {
            $user = new User(array(
                'username' => (string)$username,
                'password' => (string)$password
            ));

            $user->update();
            return $user;
        }

        return null;
    }
}

// Initialize static instance of MongoDB connection
$mongo = new \MongoClient(\OTW\Models\MONGO_SERVER);
User::$mongoDataSource = $mongo->OTW->Users;
$gcmSender = new \PHP_GCM\Sender('AIzaSyAfX_qmGNE4t_9Rp5fGOdyp-QKSnEyzbIw');
User::$gcmSenderService = $gcmSender;

?>
