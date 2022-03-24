#<AssetImports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.storage.blob import BlobServiceClient
from azure.mgmt.media.models import (Asset)
import os
#</AssetImports>

#<ClientEnvironmentVariables>
#Get environment variables
load_dotenv()

# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
default_credential = DefaultAzureCredential()

# The AMS Client 123
client = AzureMediaServices(default_credential, os.getenv("SUBSCRIPTIONID"))
#</ClientEnvironmentVariables>

#<CreateAsset>
def createAsset(account_name, resource_group_name, asset_name, alternate_id=None, description=None, storage_account=None, container=None):
  assetObj = Asset(alternate_id=alternate_id, description=description, storage_account_name=storage_account,container=container)
  thisAsset = client.assets.create_or_update(os.getenv("RESOURCEGROUP"), os.getenv("ACCOUNTNAME"), asset_name, assetObj)

createAsset(os.getenv("ACCOUNTNAME"),os.getenv("RESOURCEGROUP"),"myAsset","myAssetAlternateId","myAssetAltDesc")
#</CreateAsset>

#<DeleteAsset>
def deleteAsset(resource_group,account_name,asset_name):
  client.assets.delete(resource_group,account_name,asset_name)

deleteAsset(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"),"myAsset")
#</DeleteAsset>

#<GetAsset>
def getAsset(resource_group_name,account_name,asset_name):
  results = client.assets.get(resource_group_name,account_name,asset_name)
  print(results)

getAsset(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"),"myAsset")
#</GetAsset>

#<GetAssetEncryptionKey>
def getAssetEncKey(resource_group_name,account_name,asset_name):
  results = client.assets.get_encryption_key(resource_group_name,account_name,asset_name)
  print(results)

getAssetEncKey(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"),"myAsset")
#</GetAssetEncryptionKey>

#<ListAssets>
def listAssets(resource_group_name, account_name):
  results=client.assets.list(resource_group_name,account_name)
  # Results is a collection so you can iterate over it to get an attribute of the asset
  for result in results:
    print(result.name)

listAssets(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"))
##</ListAssets>

#<ListAssetsContainerSAS>
# TO DO
#list_container_sas(resource_group_name,account_name,asset_name, parameters: "_models.ListContainerSasInput", **kwargs: Any) -> _models.AssetContainerSas
#<ListAssetsContainerSAS>

#<ListAssetStreamingLocators>
def listStreamingLocators(resource_group_name, account_name, asset_name):
  results=client.assets.list_streaming_locators(resource_group_name,account_name,asset_name)
  streamingLocators = results.streaming_locators
  # streaminglocators is a list so you can iterate over it to get an attribute of the streaming locator
  for locator in streamingLocators:
    print(locator.name)

listStreamingLocators(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"),"myAsset")
#</ListAssetStreamingLocators>

#<UpdateAsset>
params = {
  "properties": {
    "description": "I know you are but what am I?"
  }
}
def updateAsset(resource_group_name, account_name, asset_name,parameters):
  client.assets.update(resource_group_name,account_name,asset_name,parameters)

updateAsset(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"),"myAsset",params)
#</UpdateAsset>