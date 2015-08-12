<?php

// Dependencies
require 'vendor/autoload.php';
spl_autoload_register(function ($className) {
    $classFile = str_replace(array('OTW\\', '\\'), array('', '/'),
        $className) . '.php';

    if (file_exists($classFile)) {
        require_once $classFile;
        if (class_exists($className)) {
            return true;
        }
    }
    return false;
});

// PHP Settings
date_default_timezone_set('America/Toronto');

// Slim API
$app = new \Slim\Slim();
$app->view(new \JsonApiView());
$app->add(new \JsonApiMiddleware());
$app->config('debug', true);

// Setup Routes
include __DIR__ . '/Routes/Users/index.php';
include __DIR__ . '/Routes/Users/Location/index.php';
include __DIR__ . '/Routes/Users/Location/Routes/index.php';
include __DIR__ . '/Routes/Users/Location/Grid/index.php';
include __DIR__ . '/Routes/Users/Addresses/index.php';
include __DIR__ . '/Routes/Login/index.php';
include __DIR__ . '/Routes/Login/Renew/index.php';

// Run
$app->run();

?>
