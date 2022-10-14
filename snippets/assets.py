# These code snippets are used in Azure Media Services documentation.
# DO NOT EDIT

#<AssetImports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (Asset)
import os
#</AssetImports>

#<EnvironmentVariables>
#Get environment variables
load_dotenv()

subscriptionId = os.getenv("SUBSCRIPTIONID")
accountName=os.getenv("ACCOUNTNAME")
resourceGroupName=os.getenv("RESOURCEGROUP")
clientId = os.getenv("AZURE_CLIENT_ID")
storageAccountName=os.getenv("STORAGEACCOUNTNAME")
#</EnvironmentVariables>

#<CreateAMSClient>
# Create the Media Services client and authenticate using the DefaultAzureCredential
default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)
client = AzureMediaServices(default_credential, subscriptionId)
#</CreateAMSClient>

#<CreateAsset>
#Create an Asset object
#From SDK
# Asset(*, alternate_id: Optional[str] = None, description: Optional[str] = None, container: Optional[str] = None,
# storage_account_name: Optional[str] = None, **kwargs)
assetName = "MyAsset"
assetObj = Asset(alternate_id="myAlternateId",description="My description")

#From SDK
#create_or_update(resource_group_name: str, account_name: str, asset_name: str, parameters: "_models.Asset", **kwargs: Any) -> _models.Asset
def createAsset(account_name, resource_group_name, asset_name,asset):
  thisAsset = client.assets.create_or_update(account_name, resource_group_name, asset_name,asset)

createAsset(resourceGroupName,accountName,assetName,assetObj)
#</CreateAsset>

#<GetAsset>
# Set the name of the asset for which you want to get properties.
assetName = "MyAsset"

# From SDK
# get(resource_group_name: str, account_name: str, asset_name: str, **kwargs: Any) -> _models.Asset
def getAsset(resource_group_name,account_name,asset_name):
  results = client.assets.get(resource_group_name,account_name,asset_name)
  #You can get any of the properties of an asset. Here we are printing the asset name.
  print(results.name)

getAsset(resourceGroupName,accountName,assetName)
#</GetAsset>

#<GetAssetEncryptionKey>
# Set the name of the asset for which you want to get the asset encryption key.
assetName = "MyAsset"
# From SDK
# get_encryption_key(resource_group_name: str, account_name: str, asset_name: str, **kwargs: Any) 
# -> _models.StorageEncryptedAssetDecryptionData
# If an encryption key doesn't exist yet, the results will tell you.
def getAssetEncKey(resource_group_name,account_name,asset_name):
  results = client.assets.get_encryption_key(resource_group_name,account_name,asset_name)
  print(results)

getAssetEncKey(resourceGroupName,accountName,assetName)
#</GetAssetEncryptionKey>

#<ListAssets>
# From SDK
# list(resource_group_name: str, account_name: str, 
# filter: Optional[str] = None, top: Optional[int] = None, orderby: Optional[str] = None, **kwargs: Any) 
# -> Iterable['_models.AssetCollection']
def listAssets(resource_group_name, account_name):
  results=client.assets.list(resource_group_name,account_name)
  # Results is a collection so you can iterate over it to get an attribute of the asset
  for result in results:
    print(result.name)

listAssets(resourceGroupName,accountName)
#</ListAssets>

#<ListAssetsContainerSAS>
# TO DO
#list_container_sas(resource_group_name,account_name,asset_name, parameters: "_models.ListContainerSasInput", **kwargs: Any) -> _models.AssetContainerSas
#</ListAssetsContainerSAS>

#<ListAssetStreamingLocators>
# Set the name of the asset for which you want a streaming locator list
assetName = "MyAsset"

# From SDK
# list_streaming_locators(resource_group_name: str, account_name: str, asset_name: str, **kwargs: Any) -> _models.ListStreamingLocatorsResponse
def listStreamingLocators(resource_group_name, account_name, asset_name):
  results=client.assets.list_streaming_locators(resource_group_name,account_name,asset_name)
  streamingLocators = results.streaming_locators
  # streaminglocators is a list so you can iterate over it to get an attribute of the streaming locator
  # If no streaming locators have been created for the asset, then the results will return nothing.
  for locator in streamingLocators:
    print(locator.name)

listStreamingLocators(resourceGroupName,accountName,assetName)
#</ListAssetStreamingLocators>

#<UpdateAsset>
# From SDK
# update(resource_group_name: str, account_name: str, asset_name: str, parameters: "_models.Asset", **kwargs: Any) -> _models.Asset
# Set the name of the asset that you want to update
assetName = "MyAsset"

#Create an asset object for updating
assetObj1 = Asset(description="My new description.")

def updateAsset(resource_group_name, account_name, asset_name,parameters):
  client.assets.update(resource_group_name,account_name,asset_name,assetObj1)

updateAsset(resourceGroupName,accountName,assetName,assetObj1)
#</UpdateAsset>

#<DeleteAsset>
# Set the name of the asset that you want to delete
assetName = "MyAsset"

# From SDK
# delete(resource_group_name: str, account_name: str, asset_name: str, **kwargs: Any) -> None
def deleteAsset(resource_group,account_name,asset_name):
  client.assets.delete(resource_group,account_name,asset_name)

deleteAsset(resourceGroupName,accountName,assetName)
#</DeleteAsset>
