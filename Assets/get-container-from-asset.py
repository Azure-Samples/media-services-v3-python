# This sample demonstrates how to get the container name from any Asset. It can be in input or output asset from an encoding job.
# Not that this sample also demonstrates how to name the container on creation.

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (Asset)
import os
import random

#Get environment variables
load_dotenv()


default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

# Get the environment variables SUBSCRIPTIONID, RESOURCEGROUP, ACCOUNTNAME
subscription_id = os.getenv('SUBSCRIPTIONID')
resource_group = os.getenv('RESOURCEGROUP')
account_name = os.getenv('ACCOUNTNAME')

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = random.randint(0,9999)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)

# List the Assets in Account
print("Listing assets in account:")

asset_name = 'MyCustomAssetName'
storage_container_name = 'mycustomcontainername'    # Lower case, numbers and dashes are ok. Check MSDN for more information about valid container naming

print(f"Creating a new Asset with the name: {asset_name} in storage container {storage_container_name}")
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
new_asset = Asset(alternate_id="MyCustomIdentifier", description="my description", container=storage_container_name)

asset = client.assets.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  asset_name=asset_name,
  parameters=new_asset
)

if asset:
  print("Asset created")
  print(f"This asset is in storage account '{asset.storage_account_name}' in the container '{asset.container}'")
else:
  raise Exception("There was an error while creating an asset.")

# Deleting an asset
print("Deleting asset")
client.assets.delete(resource_group, account_name, asset_name)
print("Asset is now deleted")
