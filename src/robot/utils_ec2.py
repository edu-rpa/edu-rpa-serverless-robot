import boto3
import os

ec2_client = boto3.client('ec2')

def launch_ec2(user_id, process_id, version, ami_id='ami-0d2e7d399f8a888b9'):
    robot_code_file = f'robot/{user_id}/{process_id}/{version}/robot_code.json'
    robot_folder = os.path.dirname(robot_code_file)
    user_data = f'''#!/bin/bash
    sudo yum install pip -y
    mkdir /home/ec2-user/robot && sudo chmod -R 777 /home/ec2-user/robot
    conda create -y -n robotenv python=3.9
    cd /var/lib/cloud/scripts/per-boot/
    sudo chmod -R 777 /var/lib/cloud/scripts/per-boot
    
    echo 'cd /home/ec2-user/robot \\
    && source /etc/profile.d/conda.sh \\
    && conda deactivate\\
    && conda activate robotenv \\
    && conda install -y boto3 packaging \\
    && aws s3 cp s3://robot/utils/setup.py ./ \\
    && export ROBOT_FILE={robot_code_file} \\
    && sudo chmod -R 777 /home/ec2-user/robot \\
    && python3 setup.py >> app.log\\
    && aws s3 cp ./app.log s3://{robot_folder}/run/ \\
    && aws s3 cp ./report.html s3://{robot_folder}/run/ \\
    && aws s3 cp ./log.html s3://{robot_folder}/run/ \\
    && sudo mv ./report.html ./log.html /var/www/html/.
    ' > script.sh
    
    sudo chmod 777 script.sh
    source ./script.sh
    '''

    instance_params = {
        'ImageId':ami_id,
        'InstanceType': 't3.large',
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
                        "Value": f'edu-rpa-robot.{user_id}_{process_id}_{version}'
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
