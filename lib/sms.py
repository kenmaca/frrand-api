from config import SMS_API_KEY
import requests
import json
import re

def smsSend(phoneNumber, message):
    ''' (str, str) -> bool
    Sends message to phoneNumber via SMS (by http://smsgateway.ca) and
    returns True if it was successful.
    '''

    try:
        r = requests.post(
            'http://smsgateway.ca/services/message.svc/%s/%s' % (
                SMS_API_KEY,
                re.sub(r'[^\d]+', '', phoneNumber)
            ),
            data=json.dumps(
                {
                    "MessageBody": message
                }
            ),
            headers={
                'Content-Type': 'application/json'
            }
        )

        return (
            r.json()['SendMessageWithReferenceResult']
            == 'Message queued successfully'
        )

    except Exception:
        return False
