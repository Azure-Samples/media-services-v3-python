from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (
  DefaultAction,
  StorageAccountType,
  MediaService,
  StorageAccount,
  KeyDelivery,
  AccessControl,
  CheckNameAvailabilityInput
)
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import (
  StorageAccountCheckNameAvailabilityParameters,
  StorageAccountCreateParameters,
  Sku,
  SkuName,
  Kind
)
import os
import random

# Get environment variables
load_dotenv()

# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
default_credential = DefaultAzureCredential()

# Get the environment variables SUBSCRIPTIONID and RESOURCEGROUP
subscription_id = os.getenv('SUBSCRIPTIONID')
resource_group = os.getenv('RESOURCEGROUP')

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = random.randint(0,9999)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)
storage_client = StorageManagementClient(default_credential, subscription_id)

# The New Storage Account Name that will be used
account_name = f'testaccount{uniqueness}'

# Set this to one of the available region names using the format japanwest,japaneast,eastasia,southeastasia,
# westeurope,northeurope,eastus,westus,australiaeast,australiasoutheast,eastus2,centralus,brazilsouth,
# centralindia,westindia,southindia,northcentralus,southcentralus,uksouth,ukwest,canadacentral,canadaeast,
# westcentralus,westus2,koreacentral,koreasouth,francecentral,francesouth,southafricanorth,southafricawest,
# uaecentral,uaenorth,germanywestcentral,germanynorth,switzerlandwest,switzerlandnorth,norwayeast
account_location = 'westus2'

#Create a storage account
storage_account_name = f"storageacc{uniqueness}"

# Change the stor_account_params to meet your storage needs for Media Services.
stor_avail_params = StorageAccountCheckNameAvailabilityParameters(name=storage_account_name)
stor_account_params = StorageAccountCreateParameters(
    sku=Sku(name=SkuName.STANDARD_LRS),
    kind=Kind.STORAGE,
    location='westus2',
    enable_https_traffic_only=True
    )

def create_storage(resource_group_name, storage_account_name, storage_avail_parameters, storage_account_parameters):
    # Check if the storage account name is available
    availability = storage_client.storage_accounts.check_name_availability(storage_avail_parameters)
    print('The account {} is available: {}'.format(storage_account_name, availability.name_available))
    print('Reason: {}'.format(availability.reason))
    print('Detailed message: {}'.format(availability.message))
    if not availability.name_available:
        exit()

    storage_async_operation = storage_client.storage_accounts.begin_create(
        resource_group_name,
        storage_account_name,
        storage_account_parameters
    )
    storage_account = storage_async_operation.result()
    print(storage_account)

create_storage(resource_group, storage_account_name, stor_avail_params, stor_account_params)

# Set up the values for you Media Services account
parameters = MediaService(
  location=account_location,
  storage_accounts=[
    StorageAccount(
      type=StorageAccountType.PRIMARY,
      id=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
    )
  ],
  key_delivery=KeyDelivery(
    access_control=AccessControl(
      default_action=DefaultAction.ALLOW,
      ip_allow_list=[
        # List the IPv3 addresses to Allow or Deny based on the default action.
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

if not availability.name_available:
  print(f"The account with the name {account_name} is not available.")
  print(availability.message)
  raise Exception(availability.message)

# Create a new Media Services account
response = client.mediaservices.create_or_update(resource_group, account_name, parameters)
if response:
  print(f"Successfully created account '{response.name}'.")
else:
  raise Exception("Failed to create the Media Services Account")
