from datetime import datetime
import json
from kafka import KafkaProducer, KafkaConsumer
from flask import Flask, request, jsonify
from google.ads.google_ads.client import GoogleAdsClient
from google.auth.credentials import Credentials
from google.ads.google_ads.errors import GoogleAdsException


# Set up Google Ads API client
credentials = Credentials.from_authorized_user_file('google_ads_auth.json')
client = GoogleAdsClient(credentials=credentials)

# Set up Kafka producer
producer = KafkaProducer(bootstrap_servers='localhost:9092')


app = Flask(__name__)


@app.route('/api/create_ad', methods=['POST'])
def create_ad():
    try:
        # Parse request JSON and validate required fields
        request_data = request.get_json()
        ad_group_id = request_data['ad_group_id']
        final_url = request_data['final_url']
        headline = request_data['headline']
        description = request_data['description']

        # Create ad data dictionary to be sent to Kafka
        ad_data = {
            'ad_group_id': ad_group_id,
            'final_url': final_url,
            'headline': headline,
            'description': description,
            'created_at': datetime.utcnow().isoformat()
        }

        # Send ad data to Kafka topic
        producer.send('create_ad_topic', value=json.dumps(ad_data).encode('ascii'))

        # Return success status and ad data as JSON
        return jsonify({'message': 'Ad creation request has been sent to Kafka', 'ad_data': ad_data}), 200
    except Exception as ex:
        return jsonify({'message': 'Ad creation request failed', 'error': str(ex)}), 400


# Set up Kafka consumer
consumer = KafkaConsumer(
    'create_ad_topic',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('ascii'))
)


# Consume messages and create ads
for message in consumer:
    ad_data = message.value
    try:
        ad_group_service = client.service.ad_group_ad_service
        ad_group = ad_group_service.get(ad_data['ad_group_id'])
        ad_operation = client.get_type('AdGroupAdOperation')
        ad_operation.create = ad_group_service.types.AdGroupAd()
        ad_operation.create.ad = client.get_type('Ad')
        ad_operation.create.ad.final_urls.append(ad_data['final_url'])
        ad_operation.create.ad.headline = ad_data['headline']
        ad_operation.create.ad.description = ad_data['description']
        ad_operation.create.status = client.get_type('AdGroupAdStatusEnum').PAUSED
        ad_response = ad_group_service.mutate_ad_group_ads(ad_group.id, [ad_operation])
        print(f"Ad with ID {ad_response.results[0].resource_name} created successfully!")
    except GoogleAdsException as ex:
        print(f"An error occurred while creating ad: {ex}")




'''You might want to consider configuring the Kafka producer and consumer with additional parameters like acks, retries, batch_size, and max_request_size, depending on your use case.
In production, it's also recommended to configure your Kafka topics to have more than one partition for scalability and fault tolerance.
You might want to configure logging in your Flask app and write log messages to a file or a centralized logging service.
You should also consider adding error handling and monitoring for your application, so you can detect and respond to any issues that may arise.'''