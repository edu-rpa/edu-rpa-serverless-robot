import textwrap
import boto3
import os

from .script_gen import *

from .resource_config import getCloudWatchConfig

ec2_client = boto3.client('ec2')

def launch_ec2(user_id, process_id, version, ami_id='ami-0d2e7d399f8a888b9'):
    robot_uri = f"{user_id}/{process_id}/{version}"
    robot_tag = f'edu-rpa-robot.{user_id}.{process_id}.{version}'
    robot_log_group = f'edu-rpa-robot-{user_id}-{process_id}'
    robot_bucket = os.environ["ROBOT_BUCKET"]
    robot_table = os.environ["ROBOT_TABLE"]
    cloudwatch_config = getCloudWatchConfig(robot_log_group, version)
    ###### Don't change any indent in these code !!! ######
    # Prepare env variable
    env_variables = create_env_variable(user_id, process_id, version)
    # Cloudwatch Agent Start Script
    cloudwatch_agent_start_script = cloudwatch_agent_start(cloudwatch_config,robot_table, user_id, f"{process_id}.{version}")
    # Cloudwatch Init Start Script
    cloudwatch_agent_init_script = cloudwatch_agent_init()
    # Script that ec2 run per boot
    init_script = instance_init(
        robot_bucket=robot_bucket, 
        robot_uri=robot_uri, 
        cloudwatch_agent_start=cloudwatch_agent_start_script,
    )
    
    # User data script
    user_data = textwrap.dedent(f'''
#!/bin/bash
# Install And Create Resource
sudo yum install pip jq dos2unix -y
mkdir /home/ec2-user/robot && sudo chmod -R 777 /home/ec2-user/robot
conda create -y -n robotenv python=3.9
sudo chmod -R 777 /var/lib/cloud/scripts/per-boot
touch /var/log/robot.log
aws s3 cp s3://edu-rpa-robot/utils/get-credential .
sudo chmod 755 get-credential
sudo mv ./get-credential /usr/local/bin

{env_variables}
# Init Script    
{init_script}

# Start Agent Script
{cloudwatch_agent_init_script}

# Run Robot Script
cd /var/lib/cloud/scripts/per-boot/
sudo chmod 777 script.sh
source ./script.sh
''')
    
    ###### Don't change any indent in these code !!! ######
    instance_params = {
        'ImageId':ami_id,
        'InstanceType': 't3.small',
        'MinCount': 1,
        'MaxCount': 1,
        'UserData': user_data,
        "IamInstanceProfile":{       
            'Arn': 'arn:aws:iam::678601387840:instance-profile/EC2_robot_role',
        },
        "BlockDeviceMappings":[
            {
                "DeviceName": "/dev/xvda",
                "Ebs": {
                    "VolumeSize": 15,
                    "VolumeType": "standard",
                    "DeleteOnTermination": True,
                },
            }
        ],
        "TagSpecifications": [
            {
                "ResourceType": "instance",
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": robot_tag
                    },
                ]
            }
        ]
    }
    
    # Launch the instance
    response = ec2_client.run_instances(**instance_params)
    return response["Instances"][0]
        
def start_ec2_robot(instanceId):
    response = ec2_client.start_instances(InstanceIds = [instanceId])
    return response["StartingInstances"][0]

def stop_ec2_robot(instanceId):
    response = ec2_client.stop_instances(InstanceIds = [instanceId])
    return response["StoppingInstances"][0]

def reboot_ec2_robot(instanceId):
    response = ec2_client.reboot_instances(InstanceIds = [instanceId])
    return response["StoppingInstances"][0]

def terminate_ec2_robot(instanceId):
    response = ec2_client.terminate_instances(InstanceIds = [instanceId])
    return response["TerminatingInstances"][0]
