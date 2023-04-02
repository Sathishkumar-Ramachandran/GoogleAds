import argparse
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def GetAccountDetails(client, customer_id):
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
            customer.id,
            customer.descriptive_name,
            customer.currency_code,
            customer.time_zone,
            customer.tracking_url_template,
            customer.auto_tagging_enabled
        FROM customer
        LIMIT 1"""

    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = customer_id
    request.query = query
    response = ga_service.search(request=request)
    customer = list(response)[0].customer

    print(f"Customer ID: {customer.id}")
    print(f"\tDescriptive name: {customer.descriptive_name}")
    print(f"\tCurrency code: {customer.currency_code}")
    print(f"\tTime zone: {customer.time_zone}")
    print(f"\tTracking URL template: {customer.tracking_url_template}")
    print(f"\tAuto tagging enabled: {customer.auto_tagging_enabled}")


if __name__ == "__main__":
    # GoogleAdsClient will read the google-ads.yaml configuration file in the
    # home directory if none is specified.
    googleads_client = GoogleAdsClient.load_from_storage(version="v13")

    parser = argparse.ArgumentParser(
        description=(
            "Displays basic information about the specified "
            "customer's advertising account."
        )
    )
    # The following argument(s) should be provided to run the example.
    parser.add_argument(
        "-c",
        "--customer_id",
        type=str,
        required=True,
        help="The Google Ads customer ID.",
    )
    args = parser.parse_args()

    try:
        GetAccountDetails(googleads_client, args.customer_id)
    except GoogleAdsException as ex:
        print(
            f'Request with ID "{ex.request_id}" failed with status '
            f'"{ex.error.code().name}" and includes the following errors:'
        )
        for error in ex.failure.errors:
            print(f'\tError with message "{error.message}".')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f"\t\tOn field: {field_path_element.field_name}")
        sys.exit(1)