cloudwatch_config = {
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/robot.log",
                        "log_group_name": "robot-log-group",  
                        "log_stream_name": "robot-log-stream", 
                        "timezone": "UTC"
                    }
                ]
            }
        }
    }
}