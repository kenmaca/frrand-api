<?php namespace OTW\Models\Requests;

/**
 * A representation of a Request from an User.
 */
class Request extends \OTW\Models\MongoObject
{
    // a single copy of the Collection used for all Requests
    // to avoid creating multiple wasteful connections
    public static $mongoDataSource;

    /**
     * Constructs a Request.
     *
     * @param array A 1-to-1 representation of this Request in MongoDB
     */
    public function __construct($json) {
        parent::__construct($json, self::$mongoDataSource);
    }

    /**
     * Updates this Request in MongoDB with any changes made.
     *
     * @return Request
     */
    public function update() {
        return $this->push();
    }

    /**
     * Finds Requests where the values of any specified
     * attributes in $query match those in MongoDB.
     *
     * @param array The query
     * @param boolean Whether to return each Request as an array
     *
     * @return array
     */
    public static function find($query, $asJson = false) {
        return parent::pull(self::$mongoDataSource, $query, $asJson);
    }

    /**
     * Gets a Request by its ObjectId.
     *
     * @param string The ObjectId string
     *
     * @return Request
     */
    public static function fromObjectId($objectId) {
        $request = self::find(array('_id' => new \MongoId($objectId)));
        return $request[0];
    }

    /**
     * Stores a new Request in MongoDB.
     *
     * @param array The items (as [{name: string, description: string, 
     * quantity: int, price: float}, ..])
     * @param array The available places that the items are to be picked
     * up from (as [{name: string, address: {address: string, city: string,
     * region: string, country: string, postal: string, unit: string, phone:
     * string}, coordinates: [float, float], placeId: string}, ..]
     * @param MongoDate The time that the request should be filled by
     * @param string The username of the User who initiated the request
     *
     * @return Request
     */
    public static function create($items, $places, $requestedTime, $username) {
        if (!\OTW\Models\Users\User::exists($username)
            || !$items
            || !$places
        ) {
            return null;
        }

        try {
            $requestItems = array();
            $requestPlaces = array();

            foreach($items as $item) {
                $requestItems[] = array(
                    'name' => isset($item['name']) ? (string)$item['name'] : null,
                    'description' => isset($item['description'])
                        ? (string)$item['name'] : null,
                    'quantity' => isset($item['quantity'])
                        ? (int)$item['quantity'] : 0,
                    'price' => isset($item['price']) ? (float)$item['price'] : 0
                );
            }

            foreach($places as $place) {
                $requestPlaces[] = array(
                    'name' => isset($place['name'])
                        ? (string)$place['name'] : null,
                    'address' => array(
                        'address' => isset($place['address']['address'])
                            ? $place['address']['address'] : null,
                        'city' => isset($place['address']['city'])
                            ? $place['address']['city'] : null,
                        'region' => isset($place['address']['region'])
                            ? $place['address']['region'] : null,
                        'country' => isset($place['address']['country'])
                            ? $place['address']['country'] : null,
                        'postal' => isset($place['address']['postal'])
                            ? $place['address']['postal'] : null,
                        'unit' => isset($place['address']['unit']) 
                            ? $place['address']['unit'] : null,
                        'phone' => isset($place['address']['phone'])
                            ? $place['address']['phone'] : null,
                    ),
                    'type' => 'Point',
                    'coordinates' => array(
                        isset($place['coordinates'][0])
                            ? $place['coordinates'][0] : 0,
                        isset($place['coordinates'][1])
                            ? $place['coordinates'][1] : 0
                    ),
                    'placeId' => isset($place['placeId'])
                        ? $place['placeId'] : null
                );
            }

            // finally, create the Request and save
            $newRequest = new Request(array(
                '_id' => new \MongoId(),    
                'items' => $requestItems,
                'places' => $requestPlaces,
                'username' => $username,
                'requestedTime' => $requestedTime
            ));

            return $newRequest->update();
                        
        } catch(Exception $e) {
            return null;
        }
    }
}

// Initialize static instance of MongoDB connection
$mongo = new \MongoClient(\OTW\Models\MONGO_SERVER);
Request::$mongoDataSource = $mongo->OTW->Requests;

?>
