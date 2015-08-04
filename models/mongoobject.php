<?php namespace OTW;

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
     * @return User|array
     */
    public static function pull($dataSource, $query, $asJson = false) {
        $objs = array();
        $factory = \get_called_class();

        foreach ($dataSource->find($query) as $obj) {
            $obj = new $factory($this($dataSource, $obj);
            $objs[] = $asJson ? $obj->data : $obj;
        }

        return $objs;
    }
}
