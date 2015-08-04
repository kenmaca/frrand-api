<?php namespace Users;

// the designated user field to mark as an unique identifier
define('USER_KEY', 'username');

class User
{
    private $data;
    private $dataSource = NULL;

    public function __construct($dataSource, $json = false) {
        if ($json) $this->data = $json;
        $this->dataSource = $dataSource;
    }

    public function __toString() {
        return '{' . USER_KEY . ': ' . $this->data[USER_KEY] . '}';
    }

    public function push() {

        // TODO: not really register -- will replace if user exists
        if ($this->dataSource) {
            $this->dataSource->update(array(
               USER_KEY => $this->data[USER_KEY]
            ), array(
                '$set' => $this->data
            ), array(
                'upsert' => true
            ));
        }

        return $this;
    }

    public function addAddress($street, $city, $region, $country, $postal,
        $unit = NULL) {
        if (array_key_exists('addresses', $this->data)) {
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

        return $this->push();
    }

    public function addApiKey($key, $expiry) {
        $this->data['apiKey'] = $key;
        $this->data['apiExpiry'] = $expiry;

        return $this->push();
    }

    /**
     * Produces User(s) from a data source (usually MongoDB) and
     * and links the User(s) to that data source.
     *
     * @param MongoCollection $dataSource
     * @param array $query The requested User to pull from $dataSource.
     * @param boolean $asJson Return each User as an array
     *
     * @return User|array
     */
    public static function pull($dataSource, $query, $asJson = false) {
        $users = array();
        foreach ($dataSource->find($query) as $userData) {
            $user = new User($dataSource, $userData);
            $users[] = $asJson ? $user->data : $user;
        }

        return $users;
    }

    public static function fromApiKey($dataSource, $apiKey) {
        return User::pull($dataSource, array('apiKey' => $apiKey));
    }
}

?>
