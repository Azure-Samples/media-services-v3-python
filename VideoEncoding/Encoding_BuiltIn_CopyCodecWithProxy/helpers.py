from azure.mgmt.media import AzureMediaServices
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
import os

#Get environment variables
load_dotenv()

# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
default_credential = DefaultAzureCredential()

client = AzureMediaServices(default_credential, os.getenv("SUBSCRIPTIONID"))




def getStreamingUrls(locatorName):
    # Make sure the streaming endpoint is in the "Running" state on your account
    streamingEndpoint = client.streaming_endpoints.get(
        resource_group_name = os.getenv("RESOURCEGROUP"),
        account_name = os.getenv("ACCOUNTNAME"),
        streaming_endpoint_name = "default"
    )
    
    paths = client.streaming_locators.list_paths(
        resource_group_name = os.getenv("RESOURCEGROUP"),
        account_name = os.getenv("ACCOUNTNAME"),
        streaming_locator_name = locatorName 
    )
    
    if paths.streaming_paths:
        for path in paths.streaming_paths:
            for formatPath in path.paths:
                manifest_path = "https://" + streamingEndpoint.host_name + formatPath
                print(manifest_path)
                print(f"Click to playback in AMP player: http://ampdemo.azureedge.net/?url={manifest_path}")