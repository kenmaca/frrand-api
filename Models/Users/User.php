<?php namespace OTW\Models\Users;

// the designated user field to mark as an unique identifier
define('USER_KEY', 'username');

/**
 * A representation of an User.
 */
class User extends \OTW\Models\MongoObject
{

    // a single copy of the Collection used for all Users
    // to avoid creating multiple wasteful connections
    public static $mongoDataSource;

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
    public function addAddress($name, $street, $city, $region, $country, $postal,
        $unit = null
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
     * Sets a new API key for this User.
     *
     * @param string The API key
     *
     * @return User
     */
    public function addApiKey($key) {
        $this->data['apiKey'] = $key;
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
        $user = self::find(array('apiKey' => $apiKey));
        return $user[0];
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
                'password' => (string)$password,
                'created' => new \MongoDate(),
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

?>
