import json
import os
import mysql.connector
from mysql.connector import Error

# MySQL connection configuration
mysql_config = {
    'host': os.environ['MYSQL_HOST'],
    'user': os.environ['REPORT_AGENT_SQL'],
    'password': os.environ['REPORT_AGENT_PWD'],
    'database': os.environ['REPORT_SCHEMA']
}

def trigger_write_robot_state(event, context):
    print(mysql_config)
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(**mysql_config)
        if connection.is_connected():
            print("Connected to MySQL")
            
            cursor = connection.cursor()

            # Process each record from the DynamoDB event
            for record in event['Records']:
                # Parse record data
                dynamo_data = record['dynamodb']['NewImage']
                instance_id = dynamo_data.get('instance_id', {}).get('S')
                process_id_version = dynamo_data.get('process_id_version', {}).get('S')
                user_id = dynamo_data.get('user_id', {}).get('S')
                instance_state = dynamo_data.get('instance_state', {}).get('S')
                launch_time = dynamo_data.get('launch_time', {}).get('S')
                last_run = dynamo_data.get('last_run', {}).get('S')
                description = dynamo_data.get('description', {}).get('S')

                # Write to robot_run_log table
                insert_log_query = "INSERT INTO robot_run_log (instance_id, process_id_version, user_id, instance_state, launch_time) VALUES (%s, %s, %s, %s, %s)"
                log_values = (instance_id, process_id_version, user_id, instance_state, launch_time)
                cursor.execute(insert_log_query, log_values)

                # Write to robot_run_result table if last_run field is present
                if last_run is not None:
                    insert_result_query = "INSERT INTO robot_run_result (instance_id, process_id_version, user_id, last_run, description) VALUES (%s, %s, %s, %s, %s)"
                    result_values = (instance_id, process_id_version, user_id, last_run, description)
                    cursor.execute(insert_result_query, result_values)

            # Commit changes and close cursor
            connection.commit()
            cursor.close()

    except Error as e:
        print("Error while connecting to MySQL", e)
        raise

    finally:
        if connection.is_connected():
            connection.close()
            print("MySQL connection is closed")

    return {
        'statusCode': 200,
        'body': json.dumps('Data processed successfully')
    }
