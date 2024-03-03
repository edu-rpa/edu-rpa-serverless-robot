import boto3
import json
from utils import *

def create_schedule(event, context):
    print(f'Event: {json_prettier(event)}')
    scheduler = boto3.client('scheduler')
    
    body  = json.loads(event['body'])
    user_id = body['user_id']
    process_id = body['process_id']
    version = body['version']
    schedule = body['schedule']
    start_date = body['start_date']
    end_date = body['end_date']

    schedule_name = f'edu-rpa-robot-schedule.{user_id}_{process_id}_{version}'

    try:
        schedule_response = scheduler.get_schedule(Name = schedule_name)
        return error_response(400, "Schedule Already Exists", "Cannot Create Existing Schedule")
    except scheduler.exceptions.ResourceNotFoundException:
        return handle_create_schedule(user_id, process_id, version, schedule, start_date, end_date)
    
def delete_schedule(event, context):
    print(f'Event: {json_prettier(event)}')
    scheduler = boto3.client('scheduler')
    
    body  = json.loads(event['body'])
    user_id = body['user_id']
    process_id = body['process_id']
    version = body['version']

    schedule_name = f'edu-rpa-robot-schedule.{user_id}_{process_id}_{version}'

    try:
        response = scheduler.delete_schedule(Name = schedule_name)
        return success_response(response)
    except Exception as e:
        return error_response(400, "Cannot Delete Schedule", str(e))
    
def get_schedule(event, context):
    print(f'Event: {json_prettier(event)}')
    scheduler = boto3.client('scheduler')
    
    query  = json.loads(event['queryStringParameters'])
    user_id = query['user_id']
    process_id = query['process_id']
    version = query['version']
    
    schedule_name = f'edu-rpa-robot-schedule.{user_id}_{process_id}_{version}'
    
    try:
        schedule_response = scheduler.get_schedule(Name = schedule_name)
        return success_response(schedule_response)
    except Exception as e:
        return error_response(400, "Cannot Get Schedule", str(e))
    
