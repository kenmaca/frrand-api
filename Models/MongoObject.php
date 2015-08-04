<?php namespace OTW\Models;

abstract class MongoObject
{
    private $data;
    private $dataSource = NULL;

    public function __construct($dataSource, $json = false) {
        if ($json) $this->data = $json;
        $this->dataSource = $dataSource;
    }

    public function push($key) {
        if ($this->dataSource) {
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
            $mongoObj = new $mongoFactory($dataSource, $mongoData);
            $mongoObjs[] = $asJson ? $mongoObj->data : $mongoObj;
        }

        return $mongoObjs;
    }
}

?>
