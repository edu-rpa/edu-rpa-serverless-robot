import json
import boto3

def json_prettier(jsonData) :
    return json.dumps(jsonData, indent=4, sort_keys=True, default=str)

def error_response(statusCode, error, message):
    return {
        'statusCode': statusCode,
        'body': json.dumps({
            'error': error,
            'message': message,
        })
    }

def success_response(body):
    return {
        'statusCode': 200,
        'body': json.dumps(body)
    }

def handle_create_schedule(user_id, process_id, version, schedule, start_date = None, end_date = None):
    scheduler = boto3.client('scheduler')
    schedule_name = f'edu-rpa-robot-schedule.{user_id}_{process_id}_{version}'

    create_params = {
        'Name': schedule_name,
        'FlexibleTimeWindow': {
            'Mode': 'OFF'
        },
        'Target': {
            'Arn': 'arn:aws:lambda:ap-southeast-2:678601387840:function:edu-rpa-serverless-robot-RunRobotFunction-lic2tksnLJil',
            'RoleArn': 'arn:aws:iam::678601387840:role/Robot_Scheduler_Role',
            'Input': json.dumps({
                "body": {
                    "user_id": user_id,
                    "process_id": process_id,
                    "version": version
                }
            })
        },
        'ScheduleExpression': schedule,
        'State': 'ENABLED',
    }

    if start_date:
        create_params['StartDate'] = start_date

    if end_date:
        create_params['EndDate'] = end_date

    try:
        response = scheduler.create_schedule(**create_params)
        return success_response(response)
    except Exception as e:
        return error_response(400, "Cannot Create Schedule", str(e))