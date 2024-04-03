def getCloudWatchConfig(robot_tag):
    cloudwatch_config = {
        "logs": {
            "logs_collected": {
                "files": {
                    "collect_list": [
                        {
                            "file_path": "/var/log/robot.log",
                            "log_group_name": f"robot/log/{robot_tag}",  
                            "log_stream_name": "robot_stream_$(uuidgen)", 
                            "timezone": "UTC"
                        }
                    ]
                }
            }
        }
    }
    return cloudwatch_config