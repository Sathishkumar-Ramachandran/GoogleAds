from flask import Flask, jsonify, request
from google.ads.google_ads.client import GoogleAdsClient
from google.ads.google_ads.errors import GoogleAdsException
from pymongo import MongoClient
import requests

# pip install Flask
# pip install google-ads
# pip install pymongo

app = Flask(__name__)

# Set up Google Ads API client
def get_google_ads_client():
    credentials = get_credentials()
    client = GoogleAdsClient(credentials=credentials)
    return client

# Get credentials from MongoDB
def get_credentials():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['mydatabase']
    credentials = db['credentials'].find_one()

    # Check if credentials have expired and refresh if necessary
    if is_token_expired(credentials['expires_at']):
        credentials = refresh_credentials(credentials)

    # Return Google Ads API credentials
    return credentials

# Check if token has expired
def is_token_expired(expiry_time):
    # Check if expiry time is earlier than current time
    return datetime.utcnow() > datetime.fromisoformat(expiry_time)

# Refresh credentials using the refresh token
def refresh_credentials(credentials):
    response = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': credentials['client_id'],
        'client_secret': credentials['client_secret'],
        'refresh_token': credentials['refresh_token'],
        'grant_type': 'refresh_token'
    })
    new_credentials = response.json()
    new_credentials['expires_at'] = get_expiry_time(new_credentials)
    # Update credentials in MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['mydatabase']
    db['credentials'].update_one({}, {'$set': new_credentials})
    return new_credentials

# Get expiry time of access token
def get_expiry_time(credentials):
    expires_in = credentials['expires_in']
    return (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()

# Define endpoint for changing service status
@app.route('/api/change_service_status', methods=['POST'])
def change_service_status():
    try:
        # Get Google Ads API client
        client = get_google_ads_client()

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

        # Return success status and updated service information as JSON
        return jsonify({'message': f'{service_name} status has been changed to {new_status}'}), 200
    except GoogleAdsException as ex:
        error_list = []
        for error in ex.errors:
            error_list.append(error.error_string)
        return jsonify(error_list), 400