# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (Asset)
import os
import random

#Get environment variables
load_dotenv()


default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

# Get the environment variables
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
resource_group = os.getenv('AZURE_RESOURCE_GROUP')
account_name = os.getenv('AZURE_MEDIA_SERVICES_ACCOUNT_NAME')

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = random.randint(0,9999)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)

# List the Assets in Account
print("Listing assets in account:")

asset_name = f"getcontainerfromasset{uniqueness}"
storage_container_name = f"getcontainerfromasset{uniqueness}"    # Lower case, numbers and dashes are ok. Check MSDN for more information about valid container naming

print(f"Creating a new Asset with the name: {asset_name} in storage container {storage_container_name}")
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
new_asset = Asset(alternate_id="MyCustomIdentifier", description="my description", container=storage_container_name)

asset = client.assets.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  asset_name=asset_name,
  parameters=new_asset
)

try:
  asset
  print("Asset created")
  print(f"This asset is in storage account '{asset.storage_account_name}' in the container '{asset.container}'")
except Exception as e:
  print(e)

# Delete the asset.
print("Deleting asset")
client.assets.delete(resource_group, account_name, asset_name)
print("Asset is now deleted")
