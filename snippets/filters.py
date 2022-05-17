# These code snippets are used in Azure Media Services documentation.
# DO NOT EDIT

#<FiltersImports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (
    AccountFilter,
    FirstQuality,
    AssetFilter
)
import os
#</FiltersImports>

#<EnvironmentVariables>
# Get environment variables
load_dotenv()

subscription_id = os.getenv("SUBSCRIPTIONID")
account_name=os.getenv("ACCOUNTNAME")
resource_group_name=os.getenv("RESOURCEGROUP")
client_id = os.getenv("AZURE_CLIENT_ID")
storage_account_name=os.getenv("STORAGEACCOUNTNAME")
#</EnvironmentVariables>

#<CreateAMSClient>
# Create the Media Services client and authenticate using the DefaultAzureCredential
default_credential = DefaultAzureCredential()
client = AzureMediaServices(default_credential, subscription_id)
#</CreateAMSClient>

#<CreateAccountFilter>
# Set the name of the Account filter you want to create
filter_name = "sanjaystestaccountfiltername"

# Set the properties that you want to set for the account filter
# For this sample, we want to add the first quality bitrate for the account filter.
first_quality = FirstQuality(bitrate=128000)
account_filter = AccountFilter(first_quality=first_quality)
# From SDK:
# create_or_update(resource_group_name: str, account_name: str, filter_name: str, parameters: azure.mgmt.media.models._models_py3.AccountFilter, **kwargs: Any) -> azure.mgmt.media.models._models_py3.AccountFilter
def create_account_filter(resource_group_name, account_name, filter_name, parameters):
    client.account_filters.create_or_update(resource_group_name, account_name, filter_name, parameters)
    
create_account_filter(resource_group_name, account_name, filter_name, account_filter)    
#</CreateAccountFilter>

#<GetAccountFilter>
# From SDK:
# get(resource_group_name: str, account_name: str, filter_name: str, **kwargs: Any) -> azure.mgmt.media.models._models_py3.AccountFilter
def get_account_filter(resource_group_name, account_name, filter_name):
    results = client.account_filters.get(resource_group_name, account_name, filter_name)
    # You can get any properties of account filter. Here, we are printing the account filter name.
    print(results.name)
get_account_filter(resource_group_name, account_name, filter_name)
#</GetAccountFilter>

#<ListAccountFilter>
# From SDK:
# list(resource_group_name: str, account_name: str, **kwargs: Any) -> Iterable[azure.mgmt.media.models._models_py3.AccountFilterCollection]
def list_account_filter(resource_group_name, account_name):
    results = client.account_filters.list(resource_group_name, account_name)
    # For this sample, we are printing the list of all account filters in the current Media Services Account
    for i in results:
        print(i.name) 

list_account_filter(resource_group_name, account_name)
#</ListAccountFilter>

#<UpdateAccountFilter>
# Set the properties that you want to update to the account filter
# For this sample, we want to update the first quality bitrate for the account filter.
first_quality = FirstQuality(bitrate=28000)
account_filter = AccountFilter(first_quality=first_quality)

# From SDK:
# update(resource_group_name: str, account_name: str, filter_name: str, parameters: azure.mgmt.media.models._models_py3.AccountFilter, **kwargs: Any) -> azure.mgmt.media.models._models_py3.AccountFilter
def update_account_filter(resource_group_name, account_name, filter_name, parameters):
    client.account_filters.update(resource_group_name, account_name, filter_name, parameters)
    
update_account_filter(resource_group_name, account_name, filter_name, parameters=account_filter)
#</UpdateAccountFilter>

#<DeleteAccountFilter>
# From SDK:
# delete(resource_group_name: str, account_name: str, filter_name: str, **kwargs: Any) -> None
def delete_account_filter(resource_group_name, account_name, filter_name):
    client.account_filters.delete(resource_group_name, account_name, filter_name)
    
delete_account_filter(resource_group_name, account_name, filter_name)
#</DeleteAccountFilter>

#<CreateAssetFilter>
# Set the name of the Asset filter you want to create
filter_name = "sanjaystestassetfiltername"

# For this sample, we are using an existing asset to add the asset filter. You could also create a new asset if you'd like.
asset_name = "outputassetNamemySampleRandomID"

# Set the properties that you want to set for the asset filter
# For this sample, we want to add the first quality bitrate for the asset filter.
first_quality = FirstQuality(bitrate=128000)
asset_filter = AssetFilter(first_quality=first_quality)

# From SDK:
# create_or_update(resource_group_name: str, account_name: str, asset_name: str, filter_name: str, parameters: azure.mgmt.media.models._models_py3.AssetFilter, **kwargs: Any) -> azure.mgmt.media.models._models_py3.AssetFilter
def create_asset_filter(resource_group_name, account_name, asset_name, filter_name, parameters):
    client.asset_filters.create_or_update(resource_group_name, account_name, asset_name, filter_name, parameters)
    
create_asset_filter(resource_group_name, account_name, asset_name, filter_name, parameters=asset_filter)
#</CreateAssetFilter>

#<GetAssetFilter>
# From SDK:
# get(resource_group_name: str, account_name: str, asset_name: str, filter_name: str, **kwargs: Any) -> azure.mgmt.media.models._models_py3.AssetFilter
def get_asset_filter(resource_group_name, account_name, asset_name, filter_name):
    results = client.asset_filters.get(resource_group_name, account_name, asset_name, filter_name)
    print(results.first_quality)

get_asset_filter(resource_group_name, account_name, asset_name, filter_name)
#</GetAssetFilter>

#<ListAssetFilter>
# From SDK:
# list(resource_group_name: str, account_name: str, asset_name: str, **kwargs: Any) -> Iterable[azure.mgmt.media.models._models_py3.AssetFilterCollection]
def list_asset_filter(resource_group_name, account_name, asset_name):
    results = client.asset_filters.list(resource_group_name, account_name, asset_name)
    for i in results:
        print(i.name)
        
list_asset_filter(resource_group_name, account_name, asset_name)
#</ListAssetFilter>

#<UpdateAssetFilter>
# Set the properties that you want to update to the asset filter
# For this sample, we want to update the first quality bitrate for the asset filter.
first_quality = FirstQuality(bitrate=28000)
asset_filter = AssetFilter(first_quality=first_quality)

# From SDK:
# update(resource_group_name: str, account_name: str, asset_name: str, filter_name: str, parameters: azure.mgmt.media.models._models_py3.AssetFilter, **kwargs: Any) -> azure.mgmt.media.models._models_py3.AssetFilter
def update_asset_filter(resource_group_name, account_name, asset_name, filter_name, parameters):
    client.asset_filters.update(resource_group_name, account_name, asset_name, filter_name, parameters)
    
update_asset_filter(resource_group_name, account_name, asset_name, filter_name, parameters=asset_filter)
#</UpdateAssetFilter>

#<DeleteAssetFilter>
# From SDK:
# delete(resource_group_name: str, account_name: str, asset_name: str, filter_name: str, **kwargs: Any) -> None
def delete_asset_filter(resource_group_name, account_name, asset_name, filter_name):
    client.asset_filters.delete(resource_group_name, account_name, asset_name, filter_name)
    
delete_asset_filter(resource_group_name, account_name, asset_name, filter_name)
#</DeleteAssetFilter>
