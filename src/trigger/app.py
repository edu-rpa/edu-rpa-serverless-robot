import json

def trigger_write_robot_state(event, context):
    try:
        # Process each record in the event
        for record in event['Records']:
            # Access the new and old images of the item
            new_image = record['dynamodb']['NewImage']
            old_image = record['dynamodb'].get('OldImage')

            # Your processing logic here...
            print("New Image:", json.dumps(new_image))
            if old_image:
                print("Old Image:", json.dumps(old_image))

    except Exception as e:
        print("Error processing DynamoDB stream event:", e)
        raise e  # Rethrow the error to ensure it's logged in CloudWatch
