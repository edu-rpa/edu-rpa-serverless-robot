import requests
import os

def notify_by_trigger(user_id, trigger_type, title, content):
    if trigger_type == 'manual':
        return
    
    notification_type = 'ROBOT_TRIGGER'

    url = os.environ['MAIN_SERVER_API'] + '/notification'
    headers = {
        'Content-Type': 'application/json',
        'Service-Key': os.environ['SERVICE_KEY']
    }
    body = {
        'userId': int(user_id),
        'type': notification_type,
        'title': title,
        'content': content
    }
    response = requests.post(url, headers=headers, json=body)
    print(f"Sent notification to {user_id} with result: {response.json()}")
    return response.json()
