import boto3
import json
from utils import *

def run_robot(event, context):
    print(f'Event: {json_prettier(event)}')
    robot_table = get_robot_table()

    body  = json.loads(event['body'])

    user_id = body['user_id']
    process_id = body['process_id']
    version = body['version']

    robot_response = robot_table.get_item(Key = {"userId": user_id, "processIdVersion": f'{process_id}.{version}'})

    if "Item" in robot_response:
        instance_id = robot_response["Item"]["instanceId"]
        state = robot_response["Item"]["state"]
        if state == "stopped":
            return handle_start_robot_instance(user_id, process_id, version, instance_id)
        elif state == "running":
            return error_response(400, "Robot Instance Already Running", "Cannot Start Running Instance")
        else:
            return error_response(400, "Robot Instance Not Stable", "Wait for a while and try again.")
    else:
        return handle_launch_instance(user_id, process_id, version)


def stop_robot(event, context):
    print(f'Event: {json_prettier(event)}')
    robot_table = get_robot_table()

    body  = json.loads(event['body'])

    user_id = body['user_id']
    process_id = body['process_id']
    version = body['version']

    robot_response = robot_table.get_item(Key = {"userId": user_id, "processIdVersion": f'{process_id}.{version}'})

    if "Item" in robot_response:
        instance_id = robot_response["Item"]["instanceId"]
        state = robot_response["Item"]["state"]
        if state == "running":
            return handle_stop_robot_instance(user_id, process_id, version, instance_id)
        elif state == "stopped":
            return error_response(400, "Robot Instance Already Stopped", "Cannot Stop Stopped Instance")
        else:
            return error_response(400, "Robot Instance Not Stable", "Wait for a while and try again.")
    else:
        return error_response(400, "Robot Instance Not Found", "Cannot Stop Non-Existent Instance")


def get_robot_detail(event, context):
    print(f'Event: {json_prettier(event)}')
    robot_table = get_robot_table()

    query  = json.loads(event['queryStringParameters'])

    user_id = query['user_id']
    process_id = query['process_id']
    version = query['version']

    robot_response = robot_table.get_item(Key = {"userId": user_id, "processIdVersion": f'{process_id}.{version}'})

    if "Item" in robot_response:
        return success_response(robot_response["Item"])
    else:
        return success_response({"state": "not running"})