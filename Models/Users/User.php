<?php namespace OTW\Models\Users;

// the designated user field to mark as an unique identifier
define('USER_KEY', 'username');

class User extends \OTW\Models\MongoObject
{
    public static $mongoDataSource;

    public function __construct($json) {
        parent::__construct($json, self::$mongoDataSource);
    }

    public function __toString() {
        return '{' . USER_KEY . ': ' . $this->data[USER_KEY] . '}';
    }

    public function getUsername() {
        return $this->data[USER_KEY];
    }

    public function update() {
        return $this->push(USER_KEY);
    }

    public function addAddress($street, $city, $region, $country, $postal,
        $unit = NULL
    ) {
        if (\array_key_exists('addresses', $this->data)) {
            $this->data['addresses'][] = array(
                'street' => $street,
                'city' => $city,
                'region' => $region,
                'country' => $country,
                'postal' => $postal,
                'unit' => $unit
            );
        } else {
            $this->data['addresses'] = array(array(
                'street' => $street,
                'city' => $city,
                'region' => $region,
                'country' => $country,
                'postal' => $postal,
                'unit' => $unit
            ));
        }

        return $this->update();
    }

    public function addApiKey($key, $expiry) {
        $this->data['apiKey'] = $key;
        $this->data['apiExpiry'] = $expiry;

        return $this->update();
    }

    public static function fromApiKey($apiKey) {
        return self::find(array('apiKey' => $apiKey));
    }

    public static function exists($username) {
        return self::find(array('username' => $username));
    }

    public static function all($asJson = false) {
        return self::find(array(), $asJson);
    }

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

?>
