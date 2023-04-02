import argparse
import sys
from datetime import datetime

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# [START create_customer]
def CreateAccount(client, manager_customer_id):
    customer_service = client.get_service("CustomerService")
    customer = client.get_type("Customer")
    now = datetime.today().strftime("%Y%m%d %H:%M:%S")
    customer.descriptive_name = f"Account created with CustomerService on {now}"
    # For a list of valid currency codes and time zones see this documentation:
    # https://developers.google.com/google-ads/api/reference/data/codes-formats
    customer.currency_code = "USD"
    customer.time_zone = "America/New_York"
    # The below values are optional. For more information about URL
    # options see: https://support.google.com/google-ads/answer/6305348
    customer.tracking_url_template = "{lpurl}?device={device}"
    customer.final_url_suffix = (
        "keyword={keyword}&matchtype={matchtype}" "&adgroupid={adgroupid}"
    )

    response = customer_service.create_customer_client(
        customer_id=manager_customer_id, customer_client=customer
    )
    print(
        f'Customer created with resource name "{response.resource_name}" '
        f'under manager account with ID "{manager_customer_id}".'
    )
    # [END create_customer]


if __name__ == "__main__":
    # GoogleAdsClient will read the google-ads.yaml configuration file in the
    # home directory if none is specified.
    googleads_client = GoogleAdsClient.load_from_storage(version="v13")

    parser = argparse.ArgumentParser(
        description=("Creates a new client under the given manager.")
    )
    # The following argument(s) should be provided to run the example.
    parser.add_argument(
        "-m",
        "--manager_customer_id",
        type=str,
        required=True,
        help="A Google Ads customer ID for the "
        "manager account under which the new customer will "
        "be created.",
    )
    args = parser.parse_args()

    try:
        CreateAccount(googleads_client, args.manager_customer_id)
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