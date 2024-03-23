import boto3
from botocore.exceptions import ClientError
import json
import pymysql

def get_secret():
    secret_name = "edu-rpa/dev/secrets"
    region_name = "ap-southeast-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

def get_connection(secret):
    # RDS connection parameters
    rds_host = secret.get('MYSQL_HOST')
    username = secret.get('MYSQL_USERNAME')
    password = secret.get('MYSQL_PASSWORD')
    db_name = secret.get('MYSQL_DATABASE')

    conn = None

    try:
        # Connect to the database
        conn = pymysql.connect(
            host=rds_host, 
            user=username, 
            passwd=password, 
            db=db_name, 
            connect_timeout=5,
            cursorclass=pymysql.cursors.DictCursor
        )

    except pymysql.MySQLError as e:
        print("ERROR: Unexpected error: Could not connect to MySQL instance.")
        print(e)

    return conn

def get_token(db_conn, service, user_id, connection_name):
    result = None

    try:
        with db_conn.cursor() as cursor:
            sql = f"SELECT * FROM connection WHERE provider = '{service}' AND userId = {user_id} AND name = '{connection_name}'"
            cursor.execute(sql)
            result = cursor.fetchone()
    except pymysql.MySQLError as e:
        print(e)

    return result

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
