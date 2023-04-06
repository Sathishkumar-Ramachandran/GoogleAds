from flask import Flask, request, jsonify
from google.ads.google_ads.client import GoogleAdsClient
from index import app


@app.route('/create_google_ads_account', methods=['POST'])
def create_google_ads_account():
    # Get the required parameters from the request
    manager_account_id = request.json['manager_account_id']
    new_customer_email = request.json['new_customer_email']
    time_zone = request.json['time_zone']
    currency_code = request.json['currency_code']
    payments_account_resource_name = request.json['payments_account_resource_name']
    payments_profile_id = request.json['payments_profile_id']
    tax_id = request.json['tax_id']
    conversion_tracking_id = request.json['conversion_tracking_id']
    cross_account_conversion_tracking_id = request.json['cross_account_conversion_tracking_id']
    tracking_url_template = request.json['tracking_url_template']
    final_url_suffix = request.json['final_url_suffix']

    # Set up the Google Ads API client
    client = GoogleAdsClient.load_from_storage()

    # Create a new customer account
    customer_service = client.service.customer_service
    customer = customer_service.create_customer_client(
        customer_id=manager_account_id,
        email=new_customer_email,
        access_role='ADMIN'
    )

    # Set the customer account
    client.set_client_customer_id(customer.resource_name)

    # Get the customer client service
    customer_client_service = client.service.customer_client_service

    # Set the customer's time zone
    customer_client_service.update_customer_client(
        customer_client_id=client.customer_id,
        operation={
            'update': {
                'customer_client': {
                    'time_zone': time_zone
                },
                'update_mask': ['time_zone']
            }
        }
    )

    # Set the customer's currency code
    customer_service.update_customer(
        customer={
            'resource_name': customer.resource_name,
            'currency_code': currency_code
        },
        update_mask={'paths': ['currency_code']}
    )

    # Set the customer's payment settings
    payment_settings_service = client.service.payments_account_service
    payment_settings_service.update_payments_account(
        payments_account={
            'resource_name': payments_account_resource_name,
            'currency_code': currency_code,
            'payments_profile_id': payments_profile_id,
            'time_zone': time_zone,
            'tax_info': {
                'tax_id': tax_id,
                'tax_id_type': 'OTHER'
            }
        },
        update_mask={
            'paths': [
                'currency_code',
                'payments_profile_id',
                'time_zone',
                'tax_info'
            ]
        }
    )

    # Set the customer's campaign optimization settings
    customer_service.update_customer(
        customer={
            'resource_name': customer.resource_name,
            'auto_tagging_enabled': True,
            'conversion_tracking_setting': {
                'conversion_tracking_id': conversion_tracking_id,
                'cross_account_conversion_tracking_id':
                    cross_account_conversion_tracking_id,
                'cross_account_conversion_tracking_enabled': True
            },
            'tracking_url_template': tracking_url_template,
            'final_url_suffix': final_url_suffix
        },
        update_mask={
            'paths': [
                'auto_tagging_enabled',
                'conversion_tracking_setting',
                'tracking_url_template',
                'final_url_suffix'
            ]
        }
    )

    # Return a JSON response with the new customer account ID
    response = {
        'customer_id': customer.resource_name
    }
    return jsonify(response), 200
