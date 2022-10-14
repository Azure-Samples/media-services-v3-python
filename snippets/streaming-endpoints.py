# These code snippets are used in Azure Media Services documentation.
# DO NOT EDIT

#<StreamingEndpointsImports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (StreamingEndpoint, StreamingEntityScaleUnit)
import os
#</StreamingEndpointsImports>

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
default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)
client = AzureMediaServices(default_credential, subscription_id)

# Get the media services account.
media_account = client.mediaservices.get(resource_group_name, account_name)
#</CreateAMSClient>

#<BeginCreateStreamingEndpoint>

# Set the name of the Streaming Endpoint you want to create.
streaming_endpoint_name = "mystreamingendpoint"

# Set the properties required for streaming endpoint
streaming_endpoint = StreamingEndpoint(
    location=media_account.location,
    cdn_enabled=True,
    cdn_profile="AzureMediaStreamingPlatformCdnProfile-StandardVerizon",
    cdn_provider="StandardVerizon"
)
# From SDK:
# begin_create(resource_group_name: str, account_name: str, streaming_endpoint_name: str, parameters: azure.mgmt.media.models._models_py3.StreamingEndpoint, auto_start: Optional[bool] = None, **kwargs: Any) -> azure.core.polling._poller.LROPoller[azure.mgmt.media.models._models_py3.StreamingEndpoint]
def begin_create_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name, parameters):
    streaming_endpoint = client.streaming_endpoints.begin_create(resource_group_name, account_name, streaming_endpoint_name, parameters)

begin_create_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name, parameters=streaming_endpoint)
#</BeginCreateStreamingEndpoint>

#<BeginScaleStreamingEndpoint>
# Set the number of streaming scale units for the streaming endpoint.

streaming_entity_scale_unit = StreamingEntityScaleUnit(scale_unit=2)
# From SDK:
# begin_scale(resource_group_name: str, account_name: str, streaming_endpoint_name: str, parameters: azure.mgmt.media.models._models_py3.StreamingEntityScaleUnit, **kwargs: Any) -> azure.core.polling._poller.LROPoller[None]
def begin_scale_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name, parameters):
    client.streaming_endpoints.begin_scale(resource_group_name, account_name, streaming_endpoint_name, parameters)

begin_scale_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name, parameters=streaming_entity_scale_unit)
#</BeginScaleStreamingEndpoint>

#<BeginStartStreamingEndpoint>
# From SDK:
# begin_start(resource_group_name: str, account_name: str, streaming_endpoint_name: str, **kwargs: Any) -> azure.core.polling._poller.LROPoller[None]
def begin_start_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name):
    client.streaming_endpoints.begin_start(resource_group_name, account_name, streaming_endpoint_name)

begin_start_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name)
#</BeginStartStreamingEndpoint>

#<BeginStopStreamingEndpoint>
# From SDK:
# begin_stop(resource_group_name: str, account_name: str, streaming_endpoint_name: str, **kwargs: Any) -> azure.core.polling._poller.LROPoller[None]
def begin_stop_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name):
    client.streaming_endpoints.begin_stop(resource_group_name, account_name, streaming_endpoint_name)

begin_stop_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name)
#</BeginStopStreamingEndpoint>

#<BeginUpdateStreamingEndpoint>
# Update the properties of a streaming endpoint.
# For this sample, you are updating the CDN profile to Premium Verizon

streaming_endpoint = StreamingEndpoint(
    location=media_account.location,
    cdn_profile="AzureMediaStreamingPlatformCdnProfile-PremiumVerizon",
    cdn_provider="PremiumVerizon"
)
# From SDK:
# begin_update(resource_group_name: str, account_name: str, streaming_endpoint_name: str, parameters: azure.mgmt.media.models._models_py3.StreamingEndpoint, **kwargs: Any) -> azure.core.polling._poller.LROPoller[azure.mgmt.media.models._models_py3.StreamingEndpoint]
def begin_update_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name, parameters):
    client.streaming_endpoints.begin_update(resource_group_name, account_name, streaming_endpoint_name, parameters)

begin_update_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name, parameters=streaming_endpoint)
#</BeginUpdateStreamingEndpoint>

#<GetStreamingEndpoint>
# From SDK:
# get(resource_group_name: str, account_name: str, streaming_endpoint_name: str, **kwargs: Any) -> azure.mgmt.media.models._models_py3.StreamingEndpoint
def get_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name):
    results = client.streaming_endpoints.get(resource_group_name, account_name, streaming_endpoint_name)
    # Show the name of the streaming endpoint.
    print(results.name)

get_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name)
#</GetStreamingEndpoint>

#<ListStreamingEndpoint>
# From SDK:
# list(resource_group_name: str, account_name: str, **kwargs: Any) -> Iterable[azure.mgmt.media.models._models_py3.StreamingEndpointListResult]
def list_streaming_endpoint(resource_group_name, account_name):
    results = client.streaming_endpoints.list(resource_group_name, account_name)
    # Print the names of the streaming endpoints.
    for endpoint in results:
        print(endpoint.name)

list_streaming_endpoint(resource_group_name, account_name)
#</ListStreamingEndpoint>

#<ListSkusStreamingEndpoint>
# From SDK:
# skus(resource_group_name: str, account_name: str, streaming_endpoint_name: str, **kwargs: Any) -> azure.mgmt.media.models._models_py3.StreamingEndpointSkuInfoListResult
def list_skus_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name):
    results = client.streaming_endpoints.skus(resource_group_name, account_name, streaming_endpoint_name)
    # Print the SKUs
    print(results.value)

list_skus_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name)
#</ListSkusStreamingEndpoint>

#<BeginDeleteStreamingEndpoint>
# From SDK:
# begin_delete(resource_group_name: str, account_name: str, streaming_endpoint_name: str, **kwargs: Any) -> azure.core.polling._poller.LROPoller[None]
def begin_delete_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name):
    client.streaming_endpoints.begin_delete(resource_group_name, account_name, streaming_endpoint_name)

begin_delete_streaming_endpoint(resource_group_name, account_name, streaming_endpoint_name)
#</BeginDeleteStreamingEndpoint>
