# This sample demonstrates how to get the container name from any Asset. It can be in input or output asset from an encoding job.
# Not that this sample also demonstrates how to name the container on creation.

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
import os
import random
import logging

# Acquire the logger for a library (azure.mgmt.media in this example)
logger = logging.getLogger('azure.identity')
logger.setLevel(logging.DEBUG)

logger = logging.getLogger('azure.mgmt.media')
# Set the desired logging level
logger.setLevel(logging.DEBUG)

#Get environment variables
load_dotenv()

# For details on using the DefaultAzureCredential class, see https://learn.microsoft.com/python/api/overview/azure/identity-readme?view=azure-python#authenticate-with-defaultazurecredential
default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=Trueexclude_shared_token_cache_credential=True,logging_enable=True)

# Get the environment variables SUBSCRIPTIONID, RESOURCEGROUP, ACCOUNTNAME
subscription_id = os.getenv('SUBSCRIPTIONID')
resource_group = os.getenv('RESOURCEGROUP')
account_name = os.getenv('ACCOUNTNAME')

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = random.randint(0,9999)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id, logging_enable=True)

# List the Assets in Account
print("Listing assets in account:")

# For details on how to use filters, ordering and paging see the article https://docs.microsoft.com/azure/media-services/latest/filter-order-page-entities-how-to
# Assets support filtering on name, alternateId, assetId, and created
filter_odata = "properties/alternateId eq 'MyCustomIdentifier'"
order_by = "properties/created desc"

for asset in client.assets.list(resource_group_name=resource_group, account_name=account_name, filter=filter_odata, orderby=order_by):
  print(asset.alternate_id)
