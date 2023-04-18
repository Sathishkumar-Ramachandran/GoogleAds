from flask import Flask, jsonify, request
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.ads.google_ads.client import GoogleAdsClient
from google.ads.google_ads.errors import GoogleAdsException
from models import UserAccess, UserAccessInvitation, db
from confluent_kafka import Producer

# pip install Flask
# pip install google-auth
# pip install google-ads
# pip install marshmallow
# pip install confluent-kafka

app = Flask(__name__)

# Set up Google Ads API client
credentials = Credentials.from_authorized_user_file('google_ads_auth.json')
client = GoogleAdsClient(credentials=credentials)

# Set up Kafka producer
producer_conf = {'bootstrap.servers': 'kafka-broker:9092'}
producer = Producer(producer_conf)

# Define endpoint for changing service status
@app.route('/api/change_service_status', methods=['POST'])
def change_service_status():
    try:
        # Parse request JSON and validate required fields
        request_data = request.get_json()
        service_name = request_data['service_name']
        new_status = request_data['new_status']

        # Create the Service resource with the provided information
        service = client.service(service_name)

        # Get the current status of the service
        current_status = service.get_status()

        # Check if the new status is valid
        if new_status not in service.VALID_STATUSES:
            raise ValueError(f"{new_status} is not a valid status for {service_name}")

        # If the current status is already the new status, return success
        if current_status == new_status:
            return jsonify({'message': f'{service_name} status is already {new_status}'}), 200

        # Issue a mutate operation to change the service status
        mutate_operation = service.mutate_status(new_status)
        mutate_operation.result()

        # Produce logs to Kafka topic
        log = f"{service_name} status has been changed to {new_status}"
        producer.produce('security-logs', key=service_name.encode('utf-8'), value=log.encode('utf-8'))

        # Return success status and updated service information as JSON
        return jsonify({'message': log}), 200
    except GoogleAdsException as ex:
        error_list = []
        for error in ex.errors:
            error_list.append(error.error_string)

        # Produce error logs to Kafka topic
        for error in error_list:
            producer.produce('security-logs', key=service_name.encode('utf-8'), value=error.encode('utf-8'))

        return jsonify(error_list), 400
