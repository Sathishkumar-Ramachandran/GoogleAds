from flask import Flask, jsonify, request
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.ads.google_ads.client import GoogleAdsClient
from google.ads.google_ads.errors import GoogleAdsException

app = Flask(__name__)

# Set up Google Ads API client
credentials = Credentials.from_authorized_user_file('google_ads_auth.json')
client = GoogleAdsClient(credentials=credentials)

# Define endpoint for changing event service
@app.route('/api/change_event_service', methods=['POST'])
def change_event_service():
    try:
        # Parse request JSON and validate required fields
        request_data = request.get_json()
        customer_id = request_data['customer_id']
        event_service_name = request_data['event_service_name']
        new_status = request_data['new_status']

        # Create the EventService resource with the provided information
        event_service = client.service.event_service(customer_id=customer_id, event_service_id=event_service_name)

        # Get the current status of the EventService
        current_status = event_service.get_status()

        # Check if the new status is valid
        if new_status not in event_service.VALID_STATUSES:
            raise ValueError(f"{new_status} is not a valid status for {event_service_name}")

        # If the current status is already the new status, return success
        if current_status == new_status:
            return jsonify({'message': f'{event_service_name} status is already {new_status}'}), 200

        # Issue a mutate operation to change the EventService status
        mutate_operation = event_service.mutate_status(new_status)
        mutate_operation.result()

        # Return success status and updated EventService information as JSON
        return jsonify({'message': f'{event_service_name} status has been changed to {new_status}'}), 200
    except GoogleAdsException as ex:
        error_list = []
        for error in ex.errors:
            error_list.append(error.error_string)
        return jsonify(error_list), 400



# {
#   "client_id": "YOUR_CLIENT_ID",
#   "client_secret": "YOUR_CLIENT_SECRET",
#   "refresh_token": "YOUR_REFRESH_TOKEN",
#   "access_token": "YOUR_ACCESS_TOKEN",
#   "token_uri": "https://accounts.google.com/o/oauth2/token",
#   "token_expiry": "YYYY-MM-DDTHH:MM:SSZ",
#   "user_agent": null,
#   "revoke_uri": "https://accounts.google.com/o/oauth2/revoke",
#   "id_token": null,
#   "id_token_jwt": null,
#   "expires_at": "YYYY-MM-DDTHH:MM:SSZ"
# }