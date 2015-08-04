<?php namespace OTW\Models\Users;

// the designated user field to mark as an unique identifier
define('USER_KEY', 'username');

class User extends \OTW\Models\MongoObject
{
    public function __toString() {
        return '{' . USER_KEY . ': ' . $this->data[USER_KEY] . '}';
    }

    public function update() {
        return $this->push(USER_KEY);
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

        return $this->update();
    }

    public function addApiKey($key, $expiry) {
        $this->data['apiKey'] = $key;
        $this->data['apiExpiry'] = $expiry;

        return $this->update();
    }

    public static function fromApiKey($dataSource, $apiKey) {
        return User::pull($dataSource, array('apiKey' => $apiKey));
    }
}

?>
