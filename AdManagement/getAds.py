from datetime import datetime
import json
from flask import Flask, jsonify
from google.ads.google_ads.client import GoogleAdsClient
from google.auth.credentials import Credentials
from google.ads.google_ads.errors import GoogleAdsException



#Need to add caching functionality once requested

# Set up Google Ads API client
credentials = Credentials.from_authorized_user_file('google_ads_auth.json')
client = GoogleAdsClient(credentials=credentials)

app = Flask(__name__)


@app.route('/api/ads', methods=['GET'])
def get_all_ads():
    try:
        # Get all ads
        ads_service = client.service.ad_service
        query = "SELECT ad.id, ad.final_urls, ad.headline, ad.description FROM ad"
        response = ads_service.search(query=query)

        # Build ad list
        ads = []
        for row in response:
            ad = {
                'id': row.ad.id.value,
                'final_urls': row.ad.final_urls.urls,
                'headline': row.ad.headline.value,
                'description': row.ad.description.value
            }
            ads.append(ad)

        # Return ad list as JSON
        return jsonify({'ads': ads}), 200
    except GoogleAdsException as ex:
        return jsonify({'message': 'Failed to get ads from Google Ads API', 'error': str(ex)}), 400


if __name__ == '__main__':
    app.run(debug=True)
