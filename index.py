from flask import Flask, jsonify, request
from pymongo import MongoClient
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.ads.google_ads.client import GoogleAdsClient
from google.ads.google_ads.errors import GoogleAdsException
from models import UserAccess, UserAccessInvitation, db

# pip install Flask
# pip install google-auth
# pip install google-ads
# pip install pymongo
# pip install marshmallow

app = Flask(__name__)

# Set up Google Ads API client
client = GoogleAdsClient()

# Set up MongoDB client
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['google_ads_credentials']
collection = db['credentials']

# Define endpoint for getting credentials from MongoDB
@app.route('/api/get_credentials', methods=['POST'])
def get_credentials():
    try:
        # Parse request JSON and validate required fields
        request_data = request.get_json()
        client_id = request_data['client_id']
        client_secret = request_data['client_secret']
        
        # Check if credentials exist in MongoDB
        credentials = collection.find_one({'client_id': client_id, 'client_secret': client_secret})
        if not credentials:
            return jsonify({'message': 'Credentials not found'}), 404
        
        # Check if the access token is still valid, and refresh it if necessary
        creds = Credentials.from_authorized_user_info(info=credentials)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

            # Update the access token and expiry time in the database
            new_credentials = creds.to_authorized_user_info()
            new_credentials['expires_at'] = str(creds.expiry)
            collection.update_one({'client_id': client_id, 'client_secret': client_secret},
                                   {'$set': {'access_token': new_credentials['access_token'], 
                                             'expires_at': new_credentials['expires_at']}})
        
        # Return credentials as JSON
        return jsonify({'credentials': credentials}), 200
        
    except Exception as ex:
        return jsonify({'message': str(ex)}), 500


# Define endpoint for updating credentials in MongoDB
@app.route('/api/update_credentials', methods=['PUT'])
def update_credentials():
    try:
        # Parse request JSON and validate required fields
        request_data = request.get_json()
        client_id = request_data['client_id']
        client_secret = request_data['client_secret']
        refresh_token = request_data['refresh_token']
        access_token = request_data['access_token']
        token_uri = request_data['token_uri']
        token_expiry = request_data['token_expiry']
        
        # Check if credentials exist in MongoDB
        credentials = collection.find_one({'client_id': client_id, 'client_secret': client_secret})
        if not credentials:
            return jsonify({'message': 'Credentials not found'}), 404
        
        # Update the credentials in the database
        collection.update_one({'client_id': client_id, 'client_secret': client_secret},
                               {'$set': {'refresh_token': refresh_token, 'access_token': access_token, 
                                         'token_uri': token_uri, 'expires_at': token_expiry}})
        
        # Return success message
        return jsonify({'message': 'Credentials updated successfully'}), 200
        
    except Exception as ex:
        return jsonify({'message': str(ex)}), 500
