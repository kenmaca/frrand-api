<?php namespace OTW\Models;

// server credentials
define(
    'OTW\Models\MONGO_SERVER', 
    'mongodb://otw:Triangular@localhost:27017/OTW'
);

/**
 * A base class for objects that are stored in MongoDB.
 */
abstract class MongoObject
{

    // a direct 1-to-1 with the document stored in MongoDB
    protected $data;

    // a MongoDB collection that stores this document
    protected $dataSource;

    
    /**
     * Creates a new MongoObject with the given document and collection.
     *
     * @param array|boolean A 1-to-1 representation of this Document in MongoDB
     * @param MongoCollection|boolean The collection that this Document belongs 
     * to
     */
    public function __construct($json = false, $dataSource = false) {
        if ($json) $this->data = $json;
        if ($dataSource) $this->dataSource = $dataSource;
    }

    /**
     * Updates the Document in MongoDB where the value of $key matches the
     * value of $key in this MongoObject's data array.
     *
     * @param mixed An unique attribute of this MongoObject to update by
     *
     * @return MongoObject
     */
    public function push($key = '_id') {
        if ($this->dataSource) {

            // update last updated time
            $this->data['updated'] = new \MongoDate();

            // commit the changes from data
            $this->dataSource->update(array(
               $key => $this->data[$key]
            ), array(
                '$set' => $this->data
            ), array(
                'upsert' => true
            ));
        }

        // retrieve a copy directly from MongoDB (for newly created documents)
        // wasteful, but guarantees that we have a fresh copy
        foreach($this->dataSource->find(array(
            $key => $this->data[$key]
        )) as $mongoData) {

            // assuming the $key is unique, exit on the first one found
            $this->data = $mongoData;
            return $this;
        }
    }

    /**
     * Represents this MongoObject as an array (generally for use as a JSON
     * string.
     *
     * @return array
     */
    public function asJson() {
        return $this->data;
    }

    /**
     * Gets the unique ID for this MongoObject.
     *
     * @return string
     */
    public function getObjectId() {
        return (string)$this->data['_id'];
    }

    /**
     * Produces MongoObject(s) from a data source and links the MongoObject(s)
     * to that data source.
     *
     * @param MongoCollection $dataSource
     * @param array $query The requested MongoObject to pull from $dataSource.
     * @param boolean $asJson Return each MongoObject as an array
     *
     * @return array
     */
    public static function pull($dataSource, $query, $asJson = false) {
        $mongoObjs = array();
        $mongoFactory = \get_called_class();
        $mongoQuery = $dataSource->find($query);

        foreach ($mongoQuery as $mongoData) {
            $mongoObj = new $mongoFactory($mongoData, $dataSource);
            $mongoObjs[] = $asJson ? $mongoObj->asJson() : $mongoObj;
        }

        return $mongoObjs;
    }
}

?>
