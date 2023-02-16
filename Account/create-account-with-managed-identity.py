# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# There are three scenarios where Managed Identities can be used with Media Services:
#
# 1) Granting a Media Services account access to Key Vault to enable Customer Managed Keys
# 2) Granting a Media Services account access to storage accounts to allow Media Services to bypass Azure Storage Network ACLs
# 3) Allowing other services (for example, VMs or Azure Functions) to access Media Services
#
# This sample demonstrates creating an AMS account for scenario #2.  You can modify this sample to support scenario #1 as well, just uncomment the code sections required and provide the resource information for key vault.
# Scenario 3 would be handled through the Azure Portal or CLI.
# For more information read the article - https://docs.microsoft.com/azure/media-services/latest/concept-managed-identities

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (
  DefaultAction,
  StorageAccountType,
  MediaService,
  StorageAccount,
  ResourceIdentity,
  KeyDelivery,
  AccessControl,
  AccountEncryption,
  MediaServiceIdentity,
  CheckNameAvailabilityInput
)
import os
import random

# Get environment variables
load_dotenv()


default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

# Get the environment variables
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
resource_group = os.getenv('AZURE_RESOURCE_GROUP')
storage_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
managed_identity_name = os.getenv('AZURE_USER_ASSIGNED_IDENTITY')

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = random.randint(0,9999)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)

# The New Storage Account Name and the information for Managed Identity that will be used
account_name = f'testaccount{uniqueness}'

managed_identity_resource = "/subscriptions/b05324b8-2a72-4d0c-9fef-18dfebdccfcf/resourceGroups/pythontesting_rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/pythontestingumi"
#managed_identity_resource = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{managed_identity_name}"

# Set this to one of the available region names using the format japanwest,japaneast,eastasia,southeastasia,
# westeurope,northeurope,eastus,westus,australiaeast,australiasoutheast,eastus2,centralus,brazilsouth,
# centralindia,westindia,southindia,northcentralus,southcentralus,uksouth,ukwest,canadacentral,canadaeast,
# westcentralus,westus2,koreacentral,koreasouth,francecentral,francesouth,southafricanorth,southafricawest,
# uaecentral,uaenorth,germanywestcentral,germanynorth,switzerlandwest,switzerlandnorth,norwayeast
account_location = 'westus'

#  Check if the existing storage account name exists
if storage_account_name is None:
  raise Exception("No storage account name provided in .env file.")

# Set up the values for you Media Services account
parameters = MediaService(
  location=account_location,
  storage_accounts=[
    StorageAccount(
      # This should point to an already created storage account that is Blob storage General purpose v2.
      # Recommend to use ZRS or Geo redundant ZRS in regions that support availability zones
      type=StorageAccountType.PRIMARY,
      # /subscriptions/b05324b8-2a72-4d0c-9fef-18dfebdccfcf/resourceGroups/pythontesting_rg/providers/microsoft.storage/storageaccounts/pythongtestingstor
      id="/subscriptions/b05324b8-2a72-4d0c-9fef-18dfebdccfcf/resourceGroups/pythontesting_rg/providers/microsoft.storage/storageaccounts/pythongtestingstor",
      # Set the user assigned managed identity resource and set system assigned to false here.
      identity=ResourceIdentity(
        user_assigned_identity=managed_identity_resource,
        use_system_assigned_identity=False
      )
    )
  ],
  # Sets the account encryption used. This can be changed to customer key and point to a key vault key.
  encryption=AccountEncryption(
    type="SystemKey",
    # Optional settings if using key vault encryption key and managed identity
    # identity = ResourceIdentity(
    #   user_assigned_identity = managed_identity_resource,
    #   use_system_assigned_identity = False
    # ),
    # key_vault_properties = KeyVaultProperties(
    #   key_identifier = ""
    # )
  ),
  # Enables user or system assigned managed identity when accessing storage - a.k.a - trusted storage.
  storage_authentication="ManagedIdentity",
  identity=MediaServiceIdentity(
    type="UserAssigned",
    user_assigned_identities={
      managed_identity_resource: {}
    }
  ),
  # If you plan to use a private network and do not want any streaming to
  # go out to the public internet, you can disable this account setting.
  public_network_access="Enabled",
  key_delivery=KeyDelivery(
    access_control=AccessControl(
      default_action=DefaultAction.ALLOW,
      ip_allow_list=[
        # List the IPv3 addresses to Allow or Deny based on the defaulot action.
        # "10.0.0.1/32", you can use the CIDR IPv3 format,
        # "127.0.0.1" or a single individual IPv4 address as well
      ]
    )
  )
)

availability = client.locations.check_name_availability(
  account_location,
  parameters=CheckNameAvailabilityInput(
    name=account_name,
    type="Microsoft.Media/mediaservices"
  )
)

try:
  availability.name_available
except Exception as e:
  print(f"The account with the name {account_name} is not available.")
  print(availability.message)

# Create a new Media Services account
try:
  response = client.mediaservices.begin_create_or_update(resource_group, account_name, parameters)
  print("Account created.")
except Exception as e:
  print(e)
