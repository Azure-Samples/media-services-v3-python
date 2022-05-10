# This sample demonstrates ho wto get the container name from any Asset. It can be in input or output asset from an encoding job.
# Not that this sample also demonstrates how to name the container on creation.

#<Imports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
import os
import random
#</Imports>

#<ClientEnvironmentVariables>
#Get environment variables
load_dotenv()

# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
default_credential = DefaultAzureCredential()

# Get the environment variables SUBSCRIPTIONID, RESOURCEGROUP, STORAGEACCOUNTNAME, AZURE_CLIENT_ID and AZURE_CLIENT_SECRET
SUBSCRIPTION_ID = os.getenv('SUBSCRIPTIONID')
RESOURCE_GROUP = os.getenv('RESOURCEGROUP')
ACCOUNT_NAME = os.getenv('ACCOUNTNAME')
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = random.randint(0,9999)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, SUBSCRIPTION_ID)

# List the Assets in Account
print("Listing assets in account:")

# For details on how to use filters, oderding and paging see the article https://docs.microsoft.com/azure/media-services/latest/filter-order-page-entities-how-to
# Assets support filtering on name, alternateId, assetId, and created
filter_odata = "properties/alternateId eq 'MyCustomIdentifier'"
order_by = "properties/created desc"

for asset in client.assets.list(resource_group_name=RESOURCE_GROUP, account_name=ACCOUNT_NAME, filter=filter_odata, orderby=order_by):
  print(asset.alternate_id)
