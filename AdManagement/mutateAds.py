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

# Set up Flask app
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


@app.route('/api/update_ad', methods=['PUT'])
def update_ad():
    try:
        # Parse request JSON and validate required fields
        request_data = request.get_json()
        ad_id = request_data['ad_id']
        final_url = request_data['final_url']
        headline = request_data['headline']
        description = request_data['description']

        # Update ad in Google Ads
        ad_group_service = client.service.ad_group_ad_service
        ad = ad_group_service.get(ad_id)
        ad.final_urls = [final_url]
        ad.headline = headline
        ad.description = description
        ad.status = client.get_type('AdGroupAdStatusEnum').PAUSED
        ad_operation = client.get_type('AdGroupAdOperation')
        ad_operation.update = ad
        ad_response = ad_group_service.mutate_ad_group_ads(ad.id, [ad_operation])

        #ad_response = ad_group_service.mutate_ad_group_ads(ad_group.id, [ad_operation])
        print(f"Ad with ID {ad_response.results[0].resource_name} updated successfully!")

        # Return success status and updated ad data as JSON
        updated_ad_data = {
            'ad_id': ad_id,
            'final_url': final_url,
            'headline': headline,
            'description': description,
            'updated_at': datetime.utcnow().isoformat()
        }
        return jsonify({'message': 'Ad update request has been completed', 'updated_ad_data': updated_ad_data}), 200
    except GoogleAdsException as ex:
        return jsonify({'message': 'Ad update request failed', 'error': str(ex)}), 400


@app.route('/api/delete_ad', methods=['DELETE'])
def delete_ad():
    try:
        # Parse request JSON and validate required fields
        request_data = request.get_json()
        ad_id = request_data['ad_id']

         # Delete ad from Google Ads
        ad_group_service = client.service.ad_group_ad_service
        ad_operation = client.get_type('AdGroupAdOperation')
        ad_operation.remove = ad_group_service.types.AdGroupAd()
        ad_operation.remove.resource_name = ad_id
        ad_response = ad_group_service.mutate_ad_group_ads(ad_operation=ad_operation)
        print(f"Ad with ID {ad_response.results[0].resource_name} deleted successfully!")
    
    # Return success status
        return jsonify({'message': f'Ad with ID {ad_response.results[0].resource_name} deleted successfully!'}), 200
    except GoogleAdsException as ex:
        return jsonify({'message': 'Ad deletion request failed', 'error': str(ex)}), 400