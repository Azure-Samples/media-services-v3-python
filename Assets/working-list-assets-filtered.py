# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

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
default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True,logging_enable=True)

# Get the environment variables
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
resource_group = os.getenv('AZURE_RESOURCE_GROUP')
account_name = os.getenv('AZURE_MEDIA_SERVICES_ACCOUNT_NAME')

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = random.randint(0,9999)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id, logging_enable=True)

# List all the Assets in Account
print("Listing all the assets in account:")
for asset in client.assets.list(resource_group_name=resource_group, account_name=account_name):
  print(asset.name)

substr = "output"
subtf = False

# List assets by name string substring comparison
for asset in client.assets.list(resource_group_name=resource_group, account_name=account_name):
  if substr in asset.name:
    subtf = True
  else:
    subtf = False
if subtf == False:
  print("No assets contain the substring.")
else:
  print("Listing assets by substring.")
  for asset in client.assets.list(resource_group_name=resource_group, account_name=account_name):
    if substr in asset.name:
      print(asset.name)

# For details on how to use filters, ordering and paging see the article https://docs.microsoft.com/azure/media-services/latest/filter-order-page-entities-how-to
# Assets support filtering on name, alternateId, assetId, and created

# Change MyCustomIdentifier to the alternate id of the asset you are looking for
filter_odata = "properties/alternateId eq 'MyCustomIdentifier'"
order_by = "properties/created desc"

for asset in client.assets.list(resource_group_name=resource_group, account_name=account_name, filter=filter_odata, orderby=order_by):
  print("Listing filtered assets:")
  print(asset.name)
