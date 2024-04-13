def getCloudWatchConfig(robot_log_group, robot_version):
    cloudwatch_config = {
        "logs": {
            "logs_collected": {
                "files": {
                    "collect_list": [
                        {
                            "file_path": "/var/log/robot.log",
                            "log_group_name": f"robot/log/{robot_log_group}/v{robot_version}",  
                            "log_stream_name": f"stream_$(uuidgen -r)", 
                            "timezone": "UTC"
                        }
                    ]
                }
            }
        }
    }
    return cloudwatch_config