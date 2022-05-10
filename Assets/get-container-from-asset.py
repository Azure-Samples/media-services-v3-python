# This sample demonstrates ho wto get the container name from any Asset. It can be in input or output asset from an encoding job.
# Not that this sample also demonstrates how to name the container on creation.

#<Imports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (
  Asset
)
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

asset_name = 'MyCustomAssetName'
storage_container_name = 'mycustomcontainername'    # Lowe case, numbers and dashes are ok. Check MSDN for more information about valid container naming

print(f"Creating a new Asset with the name: {asset_name} in storage container {storage_container_name}")
# From the SDK
# Asset(*, alternate_id: str = None, description: str = None, container: str = None, storage_account_name: str = None, **kwargs) -> None
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
new_asset = Asset(alternate_id="MyCustomIdentifier", description="my description", container=storage_container_name)

asset = client.assets.create_or_update(
  resource_group_name = RESOURCE_GROUP,
  account_name = ACCOUNT_NAME,
  asset_name = asset_name,
  parameters= new_asset
)

if asset is not None:
  print("Asset created")
  print(f"This asset is in storage account '{asset.storage_account_name}' in the container '{asset.container}'")
else:
  raise Exception("There was an error while creating an asset.")

"""
# Deleting an asset
print("Deleting asset")
client.assets.delete(RESOURCE_GROUP, ACCOUNT_NAME, asset_name)
print("Asset is now deleted")
"""
