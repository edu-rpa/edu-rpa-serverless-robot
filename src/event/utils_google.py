from googleapiclient.discovery import build
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
import pytz

def get_gmail_service(token, secret):
    # token is a dict with keys: userId, name, provider, refreshToken, accessToken
    creds = Credentials.from_authorized_user_info({
        'client_id': secret.get('GMAIL_CLIENT_ID'),
        'client_secret': secret.get('GMAIL_CLIENT_SECRET'),
        'refresh_token': token.get('refreshToken'),
        'token_uri': 'https://oauth2.googleapis.com/token',
        # 'scopes': ['https://www.googleapis.com/auth/gmail.readonly']
        'scopes': ['https://mail.google.com/']
    })

    service = build('gmail', 'v1', credentials=creds)

    return service

def get_drive_service(token, secret):
    creds = Credentials.from_authorized_user_info({
        'client_id': secret.get('GOOGLE_DRIVE_CLIENT_ID'),
        'client_secret': secret.get('GOOGLE_DRIVE_CLIENT_SECRET'),
        'refresh_token': token.get('refreshToken'),
        'token_uri': 'https://oauth2.googleapis.com/token',
        'scopes': ['https://www.googleapis.com/auth/drive']
    })

    service = build('drive', 'v3', credentials=creds)

    return service

def get_forms_service(token, secret):
    creds = Credentials.from_authorized_user_info({
        'client_id': secret.get('GOOGLE_FORMS_CLIENT_ID'),
        'client_secret': secret.get('GOOGLE_FORMS_CLIENT_SECRET'),
        'refresh_token': token.get('refreshToken'),
        'token_uri': 'https://oauth2.googleapis.com/token',
        'scopes': [
            'https://www.googleapis.com/auth/forms.body',
            'https://www.googleapis.com/auth/forms.responses.readonly',
            'https://www.googleapis.com/auth/drive',
        ]
    })

    service = build('forms', 'v1', credentials=creds)

    return service

def get_new_emails(service, filter):
    today = datetime.now(pytz.utc)
    query = f'after:{today.strftime("%Y/%m/%d")}'

    current_time = datetime.now(pytz.utc)
    ten_minutes_ago = current_time - timedelta(minutes=10)
    ten_minutes_ago_time = int(ten_minutes_ago.timestamp())

    try:
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q=query).execute()
        messages = results.get('messages', [])
        new_emails = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            msg_time = int(msg['internalDate'])/1000
            if msg_time > ten_minutes_ago_time and filter_email(msg, filter):
                new_emails.append(msg)
    except Exception as e:
        print(f'An error occurred: {e}')
        new_emails = []

    return new_emails

def filter_email(msg, filter):
    if filter['from'] == '' and filter['subject'] == '':
        return True

    subject = filter['subject'].lower()

    for header in msg['payload']['headers']:
        if header['name'] == 'From' and filter['from'] != '' and filter['from'] not in header['value']:
            return False
        
        if header['name'] == 'Subject' and subject != '' and subject not in header['value'].lower():
            return False
        
    return True

def get_new_files(service, filter):
    current_time = datetime.now(pytz.utc)
    ten_minutes_ago = current_time - timedelta(minutes=10)
    q = f"createdTime >= '{ten_minutes_ago.isoformat()}'"

    if filter['name'] != '':
        q += f" and name contains '{filter['name']}'"
    
    if filter['mime_type'] != '':
        q += f" and mimeType = '{filter['mime_type']}'"

    try:
        results = service.files().list(q=q).execute()
        new_files = results.get('files', [])
    except Exception as e:
        print(f'An error occurred: {e}')
        new_files = []

    return new_files

def get_new_responses(form_id, service):
    current_time = datetime.now(pytz.utc)
    ten_minutes_ago = current_time - timedelta(minutes=10)
    filter = f"timestamp >= {ten_minutes_ago.isoformat(timespec='seconds')}Z"

    try:
        results = service.forms().responses().list(formId=form_id, filter=filter).execute()
        new_responses = results.get('responses', [])
    except Exception as e:
        print(f'An error occurred: {e}')
        new_responses = []

    return new_responses