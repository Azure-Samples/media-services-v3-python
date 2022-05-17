# These code snippets are used in Azure Media Services documentation.
# DO NOT EDIT

#<StreamingPoliciesImports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (EnvelopeEncryption, EnabledProtocols, StreamingPolicy)
import os
#</StreamingPoliciesImports>

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

#<CreateStreamingPolicy>
# Set the name of the Streaming Policy you want to create
streaming_policy_name = "sanjaysteststreamingpolicy"

# Set the properties of the streaming policy
# For the sample, you are using default content key policy name and envelope encryption properties.
default_content_key_policy_name = "mycontentkeypolicy"
enabled_protocols = EnabledProtocols(
    download=False,
    dash=True,
    hls=True,
    smooth_streaming=True
)
envelope_encryption = EnvelopeEncryption(enabled_protocols=enabled_protocols)
streaming_policy = StreamingPolicy()
streaming_policy.default_content_key_policy_name=default_content_key_policy_name
streaming_policy.envelope_encryption=envelope_encryption
# From SDK:
# create(resource_group_name: str, account_name: str, streaming_policy_name: str, parameters: ._models_py3.StreamingPolicy, **kwargs: Any) -> _models_py3.StreamingPolicy
def create_streaming_policy(resource_group_name, account_name, streaming_policy_name, parameters):
    streaming_policy = client.streaming_policies.create(resource_group_name, account_name, streaming_policy_name, parameters)
    
create_streaming_policy(resource_group_name, account_name, streaming_policy_name, parameters=streaming_policy)
#</CreateStreamingPolicy>

#<DeleteStreamingPolicy>
# From SDK:
# delete(resource_group_name: str, account_name: str, streaming_policy_name: str, **kwargs: Any) -> None
def delete_streaming_policy(resource_group_name, account_name, streaming_policy_name):
    client.streaming_policies.delete(resource_group_name, account_name, streaming_policy_name)
    
delete_streaming_policy(resource_group_name, account_name, streaming_policy_name)
#</DeleteStreamingPolicy>

#<GetStreamingPolicy>
# From SDK:
# get(resource_group_name: str, account_name: str, streaming_policy_name: str, **kwargs: Any) -> _models_py3.StreamingPolicy
def get_streaming_policy(resource_group_name, account_name, streaming_policy_name):
    results = client.streaming_policies.get(resource_group_name, account_name, streaming_policy_name)
    # Print the streaming policy name.
    print(results.name)
    
get_streaming_policy(resource_group_name, account_name, streaming_policy_name)
#</GetStreamingPolicy>

#<ListStreamingPolicy>
# From SDK:
# list(resource_group_name: str, account_name: str, filter: Optional[str] = None, top: Optional[int] = None, orderby: Optional[str] = None, **kwargs: Any) -> Iterable[_models_py3.StreamingPolicyCollection]
def list_streaming_policy(resource_group_name, account_name):
    results = client.streaming_policies.list(resource_group_name, account_name)
    # Print the list of streaming policies for the Media Services account.
    for policy in results:
        print(policy.name)
        
list_streaming_policy(resource_group_name, account_name)
#</ListStreamingPolicy>
