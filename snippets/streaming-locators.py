# These code snippets are used in Azure Media Services documentation.
# DO NOT EDIT

#<StreamingLocatorsImports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (StreamingLocator)
import os
#</StreamingLocatorsImports>

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

#<CreateStreamingLocator>
# From SDK:
# create(resource_group_name: str, account_name: str, streaming_locator_name: str, parameters: _models_py3.StreamingLocator, **kwargs: Any) -> _models_py3.StreamingLocator
streaming_locator_name = "mystreaminglocator"

# Specify the name of the asset and the streaming policy you created or use one of the predefined streaming policies.
# For the purpose of this sample, you will use an existing asset named "outputassetNamemySampleRandomID" and "Predefined_ClearStreamingOnly"
# If you haven't created the asset and streaming policy, create them and use their names/identifiers with this code.
# The predefined Streaming Policies available are: 'Predefined_DownloadOnly', 'Predefined_ClearStreamingOnly', 
# 'Predefined_DownloadAndClearStreaming', 'Predefined_ClearKey', 'Predefined_MultiDrmCencStreaming' and 'Predefined_MultiDrmStreaming'.
streaming_locator = StreamingLocator(asset_name="outputassetNamemySampleRandomID", streaming_policy_name="Predefined_ClearStreamingOnly")
def create_streaming_locator(resource_group_name, account_name, streaming_locator_name, parameters):
    streaming_locator = client.streaming_locators.create(resource_group_name, account_name, streaming_locator_name, parameters)
    
create_streaming_locator(resource_group_name, account_name, streaming_locator_name, streaming_locator)
#</CreateStreamingLocator>

#<GetStreamingLocator>
# From SDK:
# get(resource_group_name: str, account_name: str, streaming_locator_name: str, **kwargs: Any) -> _models_py3.StreamingLocator
def get_streaming_locator(resource_group_name, account_name, streaming_locator_name):
    results = client.streaming_locators.get(resource_group_name, account_name, streaming_locator_name)
    # You can get any property of a streaming locator. Here, you are printing the streaming locator name.
    print(results.name)

get_streaming_locator(resource_group_name, account_name, streaming_locator_name)
#</GetStreamingLocator>

#<ListStreamingLocator>
# From SDK:
# list(resource_group_name: str, account_name: str, filter: Optional[str] = None, top: Optional[int] = None, orderby: Optional[str] = None, **kwargs: Any) -> Iterable[_models_py3.StreamingLocatorCollection]
def list_streaming_locator(resource_group_name, account_name):
    results = client.streaming_locators.list(resource_group_name, account_name)
    # List the streaming locators in the Media Services account. You can add additional functions such as filter, orderby, etc.
    for locator in results:
        print(locator.name)
        
list_streaming_locator(resource_group_name, account_name)
#</ListStreamingLocator>

#<ListStreamingLocatorContentKeys>
# From SDK:
# list_content_keys(resource_group_name: str, account_name: str, streaming_locator_name: str, **kwargs: Any) -> _models_py3.ListContentKeysResponse
def list_streaming_locator_content_keys(resource_group_name, account_name, streaming_locator_name):
    results = client.streaming_locators.list_content_keys(resource_group_name, account_name, streaming_locator_name)
    print(results.content_keys)
    
list_streaming_locator_content_keys(resource_group_name, account_name, streaming_locator_name)
#</ListStreamingLocatorContentKeys>

#<ListStreamingLocatorPaths>
# From SDK:
# list_paths(resource_group_name: str, account_name: str, streaming_locator_name: str, **kwargs: Any) -> _models_py3.ListPathsResponse
def list_streaming_locator_paths(resource_group_name, account_name, streaming_locator_name):
    results = client.streaming_locators.list_paths(resource_group_name, account_name, streaming_locator_name)
    # List the streaming locator paths
    print(results.streaming_paths)
    
list_streaming_locator_paths(resource_group_name, account_name, streaming_locator_name)
#</ListStreamingLocatorPaths>

#<DeleteStreamingLocator>
# From SDK:
# delete(resource_group_name: str, account_name: str, streaming_locator_name: str, **kwargs: Any) -> None
def delete_streaming_locator(resource_group_name, account_name, streaming_locator_name):
    client.streaming_locators.delete(resource_group_name, account_name, streaming_locator_name)
    
delete_streaming_locator(resource_group_name, account_name, streaming_locator_name)
#</DeleteStreamingLocator>
