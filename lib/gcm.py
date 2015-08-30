from gcm import GCM
from datetime import datetime
from eve.utils import date_to_rfc1123
from bson import ObjectId
from config import GCM_API_KEY

def gcmSend(deviceId, data, ttl=0):
    ''' (list of str, dict) -> bool
    Sends data via GCM to the provided deviceId and returns True
    if it worked.
    '''

    try:
        # sanitize payload first for non-serializable objects
        gcmSafe(data)

        gcmResult = GCM(GCM_API_KEY).json_request(
            registration_ids=[deviceId], data=data, time_to_live=ttl
        )

        if 'errors' in gcmResult:
            return False
        return True

    except Exception as e:
        return False

def gcmSafe(sourceDict):
    ''' (dict) -> NoneType
    Recursively mutates all non-serializable values to strings in
    sourceDict.
    '''
    
    for k, v in sourceDict.items():

        # recursive if nested dict
        if isinstance(v, dict):
            gcmSafe(v)

        # mutate datetime to rfc1123 string
        elif isinstance(v, datetime):
            sourceDict[k] = date_to_rfc1123(v)

        # mutate bson.ObjectId to string
        elif isinstance(v, ObjectId):
            sourceDict[k] = str(v)

