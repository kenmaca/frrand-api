from gcm import GCM
from settings import GCM_API_KEY

def gcmSend(deviceId, data):
    ''' (list of str, dict) -> bool
    Sends data via GCM to the provided deviceId and returns True
    if it worked.
    '''

    try:
        if ('errors' in GCM(GCM_API_KEY).json_request(
            registration_ids=[deviceId], data=data)
        ):
            return False
        return True

    except Exception:
        return False
