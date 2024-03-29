import json
import boto3
from utils_ec2 import *
from boto3.dynamodb.types import TypeDeserializer

def ddb_deserialize(r, type_deserializer = TypeDeserializer()):
    return type_deserializer.deserialize({"M": r})

def json_prettier(jsonData) :
    # NOTE: disable json prettify for CloudWatch logs
    # return json.dumps(jsonData, indent=4, sort_keys=True, default=str)
    return jsonData

def get_robot_table():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table('robot')
    return table

def get_dynamoDB_client():
    return boto3.client('dynamodb')

def get_S3_client():
    s3 = boto3.client("s3")
    return s3

def error_response(statusCode, error, message):
    return {
        'statusCode': statusCode,
        'body': json.dumps({
            'error': error,
            'message': message,
        }, default=str)
    }

def success_response(body):
    return {
        'statusCode': 200,
        'body': json.dumps(body, default=str)
    }

def handle_launch_instance(user_id, process_id, version):
    robot_table = get_robot_table()

    try:
        instance_response = launch_ec2(user_id, process_id, version)
    except Exception as e:
        return error_response(400, "Cannot Launch Robot Instance", str(e))

    instance_id = instance_response["InstanceId"]
    launch_time = instance_response["LaunchTime"]
    state = instance_response["State"]["Name"]
    process_id_version = f'{process_id}.{version}'
    robot_detail = {
        "userId": user_id,
        "processIdVersion": process_id_version,
        "launchTime": str(launch_time),
        "instanceId": instance_id,
        "instanceState": state,
    }

    try:
        robot_table.put_item(Item = robot_detail)
    except Exception as e:
        return error_response(400, "Cannot Update Robot Detail", str(e))
    
    return success_response(robot_detail)

def handle_start_robot_instance(user_id, process_id, version, instance_id):
    try:
        instance_response = start_ec2_robot(instance_id)
    except Exception as e:
        return error_response(400, "Cannot Start Robot Instance", str(e))
    
    current_state = instance_response["CurrentState"]["Name"]
    return success_response({"state": current_state})

def handle_stop_robot_instance(user_id, process_id, version, instance_id):
    try:
        instance_response = stop_ec2_robot(instance_id)
    except Exception as e:
        return error_response(400, "Cannot Stop Robot Instance", str(e))
    
    current_state = instance_response["CurrentState"]["Name"]
    return success_response({"state": current_state})

def get_instance_name(instance_id):
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response["Reservations"][0]["Instances"][0]["Tags"][0]["Value"]