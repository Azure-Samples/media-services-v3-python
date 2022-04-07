# These code snippets are used in Azure Media Services documentation.
# DO NOT EDIT

#<StorageImports>
import profile
from dotenv import load_dotenv
from azure.identity import (DefaultAzureCredential)
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (MediaServiceUpdate,StorageAccount)

from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient

from azure.mgmt.storage.models import (
    StorageAccountCheckNameAvailabilityParameters,
    StorageAccountCreateParameters,
    Sku,
    SkuName,
    Kind
)

import os
#</StorageImports>

#<EnvironmentVariables>
#Get environment variables
load_dotenv()

subscriptionId = os.getenv("SUBSCRIPTION_ID")
resourceGroupName=os.getenv("RESOURCEGROUP")
accountName = os.getenv("ACCOUNTNAME")
clientId = os.getenv("AZURE_CLIENT_ID")
#</EnvironmentVariables>

#<CreateAMSClient>
# Create the Media Services client and authenticate using the DefaultAzureCredential
#default_credential = DefaultAzureCredential()
default_credential = DefaultAzureCredential()
client = AzureMediaServices(default_credential, subscriptionId)
#</CreateAMSClient>

#<CreateStorageClient>
# Create clients for storage
resource_client = ResourceManagementClient(default_credential, subscriptionId)
storage_client = StorageManagementClient(default_credential, subscriptionId)
#</CreateStorageClient>

#<CreateStorage>
# Give a name to your storage account.
storaccountName = "mystorageaccount"

# Change the storAccountParams to meet your storage needs for Media Services.
#From SDK
#StorageAccountCheckNameAvailabilityParameters(*, name: str, **kwargs)
storAvailParams = StorageAccountCheckNameAvailabilityParameters(name=storaccountName)
storAccountParams = StorageAccountCreateParameters(
    sku=Sku(name=SkuName.standard_lrs),
    kind=Kind.storage,
    location='westus2',
    enable_https_traffic_only=True
    )

#From SDK
#check_name_availability(
# account_name: azure.mgmt.storage.v2021_08_01.models._models_py3.StorageAccountCheckNameAvailabilityParameters, **kwargs: Any)
# -> azure.mgmt.storage.v2021_08_01.models._models_py3.CheckNameAvailabilityResult

def createStorage(resource_group_name,storage_account_name,storage_avail_parameters,storage_account_parameters):
    #Check if the storage account name is available
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

createStorage(resourceGroupName,storaccountName,storAvailParams,storAccountParams)
#</CreateStorage>

#<AddStorage>
# If you created a Media Services account using the portal, then a primary storage account was created and associated with the Media Services account.
# If you created a Media Services account using any other method, a storage account is not automatically created and associated.
# For this snippet, it is assumed that you have created a Media Services account using any other method than the portal.
# If you haven't created a storage account yet, create one and come back to this snippet. Otherwise, you will get an error.

# Give your new storage account a name.
newStorageAccountName = "newstorageaccountname"

# A list to hold all of the storage accounts that are to be associated with the Media Services account.
storaccs = []

# The id for the storage account to be added to a Media Services account.
storid = f"/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Storage/storageAccounts/{newStorageAccountName}"

# Before you can add a storage account to a Media Services account, you have to list the storage accounts that are already
# associated with the Media Services account, and add them to the storage accounts list. For this sample, it is called storaccs.

# Get a list of storage accounts for the Media Services account
results = client.mediaservices.list(resourceGroupName)
# Returns all the Media Services accounts in a resource group.
# Define which Media Services account you want to add storage to.
amsAccount = "myamsaccount"
newStorage = StorageAccount(type="Primary", id=storid)

for accounts in results:
    # If the Media Services account is found in the accounts list,
    # get the storage accounts that exist for that Media Services account.
        for storage in accounts.storage_accounts:
            if amsAccount == accounts.name:
                storaccs.append(storage)

# Count the number of storage accounts
storCount = len(storaccs)

# There can be only one primary storage account associated with a Media Services account.
# If the Media Services account doesn't yet have a primary storage account, the type value is "Primary".
# If the Media Services account does have a primary storage account, the type value is "Secondary".

if(storCount > 0):
    newStorage = StorageAccount(type="Secondary",id=storid)
else:
    newStorage = StorageAccount(type="Primary", id=storid)

# Check to see if the new storage account already exists
# in the storaccs list.

if newStorage in storaccs:
    print("The new storage account is already associated with the Media Services account.")
    exit()
else:
    storaccs.append(newStorage)

# Create an update object to send to the update
update = MediaServiceUpdate(storage_accounts=storaccs)

# Update the storage account
client.mediaservices.update(resourceGroupName,accountName,update)
#</AddStorage>

#<RemoveStorage>
# Get a list of storage accounts for the Media Services account
results = client.mediaservices.list(resourceGroupName)
# Returns all the Media Services accounts in a resource group.
# Define which Media Services account you want to add storage to.
amsAccount = "myamsaccount"
remAccountId = "/subscriptions/b05324b8-2a72-4d0c-9fef-18dfebdccfcf/resourceGroups/ingridsrg/providers/Microsoft.Storage/storageAccounts/ingridsstorageaccount2"
storaccs = []

for accounts in results:
    # If the Media Services account is found in the accounts list,
    # get the storage accounts that exist for that Media Services account.
        for storage in accounts.storage_accounts:
            if amsAccount == accounts.name:
                if storage.id == remAccountId:
                    print("storage account found")
                    #Skip it and don't add it to the storaccs list
                else:
                    storaccs.append(storage)

print(storaccs)

update = MediaServiceUpdate(storage_accounts=storaccs)
client.mediaservices.update(resourceGroupName,accountName,update)
#</RemoveStorage>

#<SyncStorageKeys>
# TO DO
#</SyncStorageKeys>
