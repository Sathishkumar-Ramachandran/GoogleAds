from flask import Flask, jsonify, request
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.ads.google_ads.client import GoogleAdsClient
from google.ads.google_ads.errors import GoogleAdsException

app = Flask(__name__)

# Set up Google Ads API client
credentials = Credentials.from_authorized_user_file('google_ads_auth.json')
client = GoogleAdsClient(credentials=credentials)

# Define endpoint for listing accessible accounts
@app.route('/api/list_accessible_accounts', methods=['GET'])
def list_accessible_accounts():
    try:
        # Create a service object for the CustomerService
        customer_service = client.service("CustomerService")

        # Get the list of accessible customers for the authenticated Google Ads account
        response = customer_service.list_accessible_customers()

        # Extract the customer ID and descriptive name for each accessible customer
        customers = []
        for customer in response.resource_names:
            customer_id = customer.split('/')[-1]
            customer_info = client.get_service('CustomerService').get_customer(customer_id)
            customers.append({
                'customer_id': customer_id,
                'descriptive_name': customer_info.descriptive_name
            })

        # Return the list of accessible customers as JSON
        return jsonify(customers), 200

    except GoogleAdsException as ex:
        error_list = []
        for error in ex.errors:
            error_list.append(error.error_string)
        return jsonify(error_list), 400
