<?php namespace OTW\Models\Users;

/**
 * A object with GCM sending capabilities.
 */
interface GCMSender
{
    /**
     * Sends $payload to this GCMSender via GCM.
     *
     * @param array The payload to send
     */
    public function gcmSend($payload, $collapseKey = '');
}

?>
