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
    create_schedule_dto = body['create_schedule_dto']

    schedule_name = f'edu-rpa-robot-schedule.{user_id}.{process_id}.{version}'

    try:
        schedule_response = scheduler.get_schedule(Name = schedule_name)
        return error_response(400, "Schedule Already Exists", "Cannot Create Existing Schedule")
    except scheduler.exceptions.ResourceNotFoundException:
        return handle_create_schedule(user_id, process_id, version, create_schedule_dto)
    
def delete_schedule(event, context):
    print(f'Event: {json_prettier(event)}')
    scheduler = boto3.client('scheduler')
    
    body  = json.loads(event['body'])
    user_id = body['user_id']
    process_id = body['process_id']
    version = body['version']

    schedule_name = f'edu-rpa-robot-schedule.{user_id}.{process_id}.{version}'

    try:
        response = scheduler.delete_schedule(Name = schedule_name)
        return success_response(response)
    except Exception as e:
        return error_response(400, "Cannot Delete Schedule", str(e))
    
def get_schedule(event, context):
    print(f'Event: {json_prettier(event)}')
    scheduler = boto3.client('scheduler')
    
    query  = event['queryStringParameters']
    user_id = query['user_id']
    process_id = query['process_id']
    version = query['version']
    
    schedule_name = f'edu-rpa-robot-schedule.{user_id}.{process_id}.{version}'
    
    try:
        schedule_response = scheduler.get_schedule(Name = schedule_name)
        return success_response(schedule_response)
    except scheduler.exceptions.ResourceNotFoundException:
        return success_response({})
    except Exception as e:
        return error_response(400, "Cannot Get Schedule", str(e))
    
def update_schedule(event, context):
    print(f'Event: {json_prettier(event)}')
    scheduler = boto3.client('scheduler')
    
    body  = json.loads(event['body'])
    user_id = body['user_id']
    process_id = body['process_id']
    version = body['version']
    update_schedule_dto = body['update_schedule_dto']

    schedule_name = f'edu-rpa-robot-schedule.{user_id}.{process_id}.{version}'

    try:
        schedule_response = scheduler.get_schedule(Name = schedule_name)
        return handle_update_schedule(user_id, process_id, version, update_schedule_dto)
    except scheduler.exceptions.ResourceNotFoundException:
        return error_response(400, "Schedule Not Found", "Cannot Update Non-Existing Schedule")
    
