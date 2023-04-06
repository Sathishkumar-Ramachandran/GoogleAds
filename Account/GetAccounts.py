import asyncio
from flask import Flask, jsonify
from google.ads.google_ads.client import GoogleAdsClient
from google.ads.google_ads.errors import GoogleAdsException
from index import app


async def get_google_ads_accounts():
    client = await GoogleAdsClient.load_from_storage()
    query = f"SELECT customer_client.id, customer_client.descriptive_name, customer_client.currency_code FROM customer_client"
    response = await client.service.google_ads_service.search(query=query, page_size=10000)
    return [
        {
            "id": str(account.customer_client.id.value),
            "name": account.customer_client.descriptive_name.value,
            "currency": account.customer_client.currency_code.value,
        }
        for account in response
    ]




@app.route('/accounts')
def get_accounts():
    try:
        # Initialize a GoogleAdsClient instance with your credentials
        client = GoogleAdsClient.load_from_storage()

        # Define a query to retrieve all accounts
        query = """
            SELECT 
                customer_client.client_customer, 
                customer_client.descriptive_name 
            FROM 
                customer_client"""

        # Execute the query
        response = client.service.customer.list_accessible_customers(
            query=query,
            page_size=1000  # Change this to retrieve more results
        )

        # Build a list of account dictionaries
        accounts = []
        for result in response.results:
            account = {
                "id": result.customer_client.client_customer,
                "name": result.customer_client.descriptive_name
            }
            accounts.append(account)

        # Return the list of accounts as a JSON response
        return jsonify(accounts)

    except GoogleAdsException as ex:
        # Handle any errors that occur
        error_message = f"Request with ID '{ex.request_id}' failed with status " \
                        f"'{ex.error.code().name}' and includes the following errors:"
        errors = []
        for error in ex.failure.errors:
            error_dict = {
                "code": error.error_code,
                "message": error.message
            }
            errors.append(error_dict)
        response = {
            "error": error_message,
            "errors": errors
        }
        return jsonify(response), 500  # Return an HTTP 500 error response
@app.route("/accounts/<string:account_id>", methods=["GET"])
async def get_account(account_id):
    loop = asyncio.get_event_loop()
    accounts = await loop.run_in_executor(None, get_google_ads_accounts)
    account = next((account for account in accounts if account["id"] == account_id), None)
    if account is None:
        return jsonify({"error": "Account not found"}), 404
    return jsonify(account)