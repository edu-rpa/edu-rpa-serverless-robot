import json
import boto3
import os

from .resource_config import getCloudWatchConfig

ec2_client = boto3.client('ec2')

def launch_ec2(user_id, process_id, version, ami_id='ami-0d2e7d399f8a888b9'):
    robot_code_file = f'robot/{user_id}/{process_id}/{version}/robot_code.json'
    robot_folder = os.path.dirname(robot_code_file)
    robot_tag = f'edu-rpa-robot.{user_id}.{process_id}.{version}'
    robot_log_group = f'edu-rpa-robot-{user_id}-{process_id}'
    robot_bucket = os.environ["ROBOT_BUCKET"]
    cloudwatch_agent_script = f'''cd /tmp
        wget https://s3.ap-southeast-1.amazonaws.com/amazoncloudwatch-agent-ap-southeast-1/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
        rpm -U ./amazon-cloudwatch-agent.rpm
        echo '{json.dumps(getCloudWatchConfig(robot_log_group, version), indent=4)}'  > /opt/aws/amazon-cloudwatch-agent/bin/config.json
        sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json
    '''
    
    user_data = f'''#!/bin/bash
    sudo yum install pip jq -y
    mkdir /home/ec2-user/robot && sudo chmod -R 777 /home/ec2-user/robot
    conda create -y -n robotenv python=3.9
    cd /var/lib/cloud/scripts/per-boot/
    sudo chmod -R 777 /var/lib/cloud/scripts/per-boot
    touch /var/log/robot.log
    
    echo 'cd /home/ec2-user/robot \\
    && source /etc/profile.d/conda.sh \\
    && conda deactivate\\
    && conda activate robotenv \\
    && conda install -y boto3 packaging \\
    && aws s3 cp s3://{robot_bucket}/utils/setup.sh ./ \\
    && export ROBOT_FILE={robot_code_file} \\
    && sudo chmod -R 777 /home/ec2-user/robot \\
    && bash setup.sh >> /var/log/robot.log \\
    && aws s3 cp /var/log/robot.log s3://{robot_bucket}/{robot_folder}/run/ \\
    && aws s3 cp ./report.html s3://{robot_bucket}/{robot_folder}/run/ \\
    && aws s3 cp ./log.html s3://{robot_bucket}/{robot_folder}/run/ \\
    && sudo mv ./report.html ./log.html /var/www/html/.
    ' > script.sh
    
    ${cloudwatch_agent_script}
    sudo chmod 777 script.sh
    source ./script.sh
    '''

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
