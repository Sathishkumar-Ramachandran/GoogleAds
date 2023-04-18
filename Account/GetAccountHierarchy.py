from flask import Flask, request, jsonify
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

app = Flask(__name__)

@app.route('/getaccountdetails')
def get_account_details():
    login_customer_id = request.args.get('login_customer_id')
    if not login_customer_id:
        return 'Error: Please provide a login_customer_id.'

    try:
        # Create the Google Ads client using the configuration file.
        googleads_client = GoogleAdsClient.load_from_storage()

        # Call the main method to get the account hierarchy.
        accounts_hierarchy = main(googleads_client, login_customer_id)

        # Return the accounts hierarchy as a JSON response.
        return jsonify(accounts_hierarchy)

    except GoogleAdsException as ex:
        return 'Error: An error occurred while getting the account hierarchy - {}'.format(ex.message)

def main(client, login_customer_id=None):
    """Gets the account hierarchy of the given MCC and login customer ID.

    Args:
      client: The Google Ads client.
      login_customer_id: Optional manager account ID. If none provided, this
      method will instead list the accounts accessible from the
      authenticated Google Ads account.
    """

    # Gets instances of the GoogleAdsService and CustomerService clients.
    googleads_service = client.get_service("GoogleAdsService")
    customer_service = client.get_service("CustomerService")

    # A collection of customer IDs to handle.
    seed_customer_ids = []

    # Creates a query that retrieves all child accounts of the manager
    # specified in search calls below.
    query = """
        SELECT
          customer_client.client_customer,
          customer_client.level,
          customer_client.manager,
          customer_client.descriptive_name,
          customer_client.currency_code,
          customer_client.time_zone,
          customer_client.id
        FROM customer_client
        WHERE customer_client.level <= 1"""

    # If a Manager ID was provided in the customerId parameter, it will be
    # the only ID in the list. Otherwise, we will issue a request for all
    # customers accessible by this authenticated Google account.
    if login_customer_id is not None:
        seed_customer_ids = [login_customer_id]
    else:
        accounts_hierarchy = []
        customer_resource_names = (
            customer_service.list_accessible_customers().resource_names
        )

        for customer_resource_name in customer_resource_names:
            customer_id = googleads_service.parse_customer_path(
                customer_resource_name
            )["customer_id"]
            seed_customer_ids.append(customer_id)

    accounts_hierarchy = []
    for seed_customer_id in seed_customer_ids:
        # Performs a breadth-first search to build a Dictionary that maps
        # managers to their child accounts (customerIdsToChildAccounts).
        unprocessed_customer_ids = [seed_customer_id]
        customer_ids_to_child_accounts = dict()
        root_customer_client = None

        while unprocessed_customer_ids:
            customer_id = int(unprocessed_customer_ids.pop(0))
            response = googleads_service.search(
                customer_id=str(customer_id), query=query
            )

            # Iterates over all rows in all pages to get all customer
            # clients under the specified customer's hierarchy.
            for googleads_row in response:
                customer_client = googleads_row.customer_client

                # The customer client that with level 
            # 0 is the manager account.
            if customer_client.level == 0:
                root_customer_client = customer_client
                continue

            # Adds the customer ID to the map with a reference to the
            # customer client.
            if customer_client.manager in customer_ids_to_child_accounts:
                customer_ids_to_child_accounts[customer_client.manager].append(
                    customer_client
                )
            else:
                customer_ids_to_child_accounts[customer_client.manager] = [
                    customer_client
                ]

            # Adds the customer ID to the list of unprocessed customers.
            if customer_client.client_customer in customer_ids_to_child_accounts:
                unprocessed_customer_ids.append(customer_client.id)

    # Converts the customer ID map into a hierarchy.
    hierarchy = convert_customer_id_map_to_hierarchy(
        customer_ids_to_child_accounts, root_customer_client
    )

    accounts_hierarchy.append(hierarchy)

    return accounts_hierarchy


def convert_customer_id_map_to_hierarchy(
        customer_ids_to_child_accounts, root_customer_client
):
    """Converts a map of customer IDs to their child accounts into a dictionary
    representing a hierarchy of accounts.

    Args:
      customer_ids_to_child_accounts: A dictionary mapping customer IDs to their
          child accounts.
      root_customer_client: The root customer client for the hierarchy.

    Returns:
      A dictionary representing the hierarchy of accounts.
    """
    hierarchy = {
        "id": root_customer_client.id,
        "name": root_customer_client.descriptive_name,
        "currency_code": root_customer_client.currency_code,
        "time_zone": root_customer_client.time_zone,
    }

    if root_customer_client.id in customer_ids_to_child_accounts:
        hierarchy["child_accounts"] = [
            convert_customer_id_map_to_hierarchy(
                customer_ids_to_child_accounts, child
            )
            for child in customer_ids_to_child_accounts[root_customer_client.id]
        ]

    return hierarchy


if __name__ == "__main__":
    app.run()