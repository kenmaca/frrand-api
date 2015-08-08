<?php namespace OTW\Models;

// server credentials
define('OTW\Models\MONGO_SERVER', 'mongodb://otw:Triangular@localhost:27017/OTW');

abstract class MongoObject
{
    protected $data;
    protected $dataSource;

    public function __construct($json = false, $dataSource = false) {
        if ($json) $this->data = $json;
        if ($dataSource) $this->dataSource = $dataSource;
    }

    public function push($key) {
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

        return $this;
    }

    public function asJson() {
        return $this->data;
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
