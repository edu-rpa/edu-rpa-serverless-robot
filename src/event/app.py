from utils import *
from utils_google import *
import boto3

def check_new_emails(event, context):
    print(f'Event: {event}')

    secret = get_secret()
    db_conn = get_connection(secret)
    if db_conn is None:
        return error_response(500, 'Failed to connect to database')
    
    user_id = event['user_id']
    process_id = event['process_id']
    version = event['version']
    connection_name = event['connection_name']
    filter = event['filter']
    service = 'Gmail'

    token = get_token(db_conn, service, user_id, connection_name)

    print(f'Successfully retrieved token of: {token.get("name")} for service: {service}')

    service = get_gmail_service(token, secret)
    new_emails = get_new_emails(service, filter)

    print(f'Found {len(new_emails)} new emails')
    if len(new_emails) == 0:
        return success_response('No new emails found')

    event_type = 'event-gmail'
    return run_robot_with_event(user_id, process_id, version, event_type, new_emails)

def check_new_files(event, context):
    print(f'Event: {event}')

    secret = get_secret()
    db_conn = get_connection(secret)
    if db_conn is None:
        return error_response(500, 'Failed to connect to database')
    
    user_id = event['user_id']
    process_id = event['process_id']
    version = event['version']
    connection_name = event['connection_name']
    filter = event['filter']
    service = 'Google Drive'

    token = get_token(db_conn, service, user_id, connection_name)

    print(f'Successfully retrieved token of: {token.get("name")} for service: {service}')

    service = get_drive_service(token, secret)
    new_files = get_new_files(service, filter)

    print(f'Found {len(new_files)} new files')
    if len(new_files) == 0:
        return success_response('No new files found')
    
    event_type = 'event-drive'
    return run_robot_with_event(user_id, process_id, version, event_type, new_files)

def check_new_responses(event, context):
    print(f'Event: {event}')

    secret = get_secret()
    db_conn = get_connection(secret)
    if db_conn is None:
        return error_response(500, 'Failed to connect to database')
    
    user_id = event['user_id']
    process_id = event['process_id']
    version = event['version']
    connection_name = event['connection_name']
    form_id = event['form_id']
    service = 'Google Forms'

    token = get_token(db_conn, service, user_id, connection_name)

    print(f'Successfully retrieved token of: {token.get("name")} for service: {service}')

    service = get_forms_service(token, secret)
    new_responses = get_new_responses(form_id, service)

    print(f'Found {len(new_responses)} new responses')
    if len(new_responses) == 0:
        return success_response('No new responses found')
    
    event_type = 'event-forms'
    return run_robot_with_event(user_id, process_id, version, event_type, new_responses)

def upsert_event_schedule(event, context):
    print(f'Event: {event}')
    scheduler = boto3.client('scheduler')
    
    body  = json.loads(event['body'])
    user_id = body['user_id']
    process_id = body['process_id']
    version = body['version']
    event_schedule = body['event_schedule']

    schedule_name = f'edu-rpa-robot-schedule.{user_id}.{process_id}.{version}'

    try:
        schedule_response = scheduler.get_schedule(Name = schedule_name)
        return handle_update_event_schedule(user_id, process_id, version, event_schedule, schedule_response)
    except scheduler.exceptions.ResourceNotFoundException:
        return handle_create_event_schedule(user_id, process_id, version, event_schedule)
