from utils import *
from utils_google import *

secret = get_secret()
db_conn = get_connection(secret)

def check_new_emails(event, context):
    print(f'Event: {event}')

    if db_conn is None:
        return error_response(500, 'Failed to connect to database')
    
    query = event['queryStringParameters']
    user_id = query['user_id']
    connection_name = query['connection_name']
    service = 'Gmail'

    token = get_token(db_conn, service, user_id, connection_name)

    print(f'Successfully retrieved token of: {token.get("name")} for service: {service}')

    service = get_gmail_service(token, secret)
    new_emails = get_new_emails(service)

    print(f'Found {len(new_emails)} new emails')

    return success_response(new_emails)
