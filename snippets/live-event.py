# These code snippets are used in Azure Media Services documentation.
# DO NOT EDIT

#<LiveEventImports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (
    LiveEvent,
    LiveEventEncoding,
    LiveEventEncodingType,
    LiveEventInput,
    LiveEventInputProtocol,
    StreamOptionsFlag,
    LiveEventActionInput
)
import os
#</LiveEventImports>

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

# Get the media services account object for information on the current location.
media_account = client.mediaservices.get(resource_group_name, account_name)
#</CreateAMSClient>

#<CreateLiveEvent>
# Set the name of the live event you want to create
live_event_name = "myliveevent"

# Set the properties that you want to set for the live event
# For this sample, we want to add the location, encoding, live event input and stream options
live_event = LiveEvent(
    location=media_account.location,
    input=LiveEventInput(
        streaming_protocol=LiveEventInputProtocol.RTMP
    ),
    encoding=LiveEventEncoding(
        encoding_type=LiveEventEncodingType.PREMIUM1080_P,
        preset_name="default1080p"
    ),
    use_static_hostname=True,
    hostname_prefix=live_event_name,
    stream_options=[StreamOptionsFlag.DEFAULT]
)

# From SDK:
# begin_create(resource_group_name: str, account_name: str, live_event_name: str, parameters: azure.mgmt.media.models._models_py3.LiveEvent,
# auto_start: Optional[bool] = None, **kwargs: Any) -> azure.core.polling._poller.LROPoller[azure.mgmt.media.models._models_py3.LiveEvent]
def create_live_event(resource_group_name, account_name, live_event_name, parameters):
    client.live_events.begin_create(resource_group_name, account_name, live_event_name, parameters)
    
create_live_event(resource_group_name, account_name, live_event_name, parameters=live_event)
#</CreateLiveEvent>

#<AllocateLiveEvent>
# From SDK:
# begin_allocate(resource_group_name: str, account_name: str, live_event_name: str, **kwargs: Any) -> azure.core.polling._poller.LROPoller[None]
def allocate_live_event(resource_group_name, account_name, live_event_name):
    client.live_events.begin_allocate(resource_group_name, account_name, live_event_name)
    
allocate_live_event(resource_group_name, account_name, live_event_name)
#</AllocateLiveEvent>

#<ResetLiveEvent>
# From SDK:
# begin_reset(resource_group_name: str, account_name: str, live_event_name: str, **kwargs: Any) -> azure.core.polling._poller.LROPoller[None]
def reset_live_event(resource_group_name, account_name, live_event_name):
    client.live_events.begin_reset(resource_group_name, account_name, live_event_name)
    
reset_live_event(resource_group_name, account_name, live_event_name)
#</ResetLiveEvent>

#<StartLiveEvent>
# From SDK:
# begin_start(resource_group_name: str, account_name: str, live_event_name: str, **kwargs: Any) -> azure.core.polling._poller.LROPoller[None]
def start_live_event(resource_group_name, account_name, live_event_name):
    client.live_events.begin_start(resource_group_name, account_name, live_event_name)
    
start_live_event(resource_group_name, account_name, live_event_name)
#</StartLiveEvent>

#<StopLiveEvent>
parameters = LiveEventActionInput(remove_outputs_on_stop=True)
# From SDK:
# begin_stop(resource_group_name: str, account_name: str, live_event_name: str, parameters: azure.mgmt.media.models._models_py3.LiveEventActionInput, **kwargs: Any) -> azure.core.polling._poller.LROPoller[None]
def stop_live_event(resource_group_name, account_name, live_event_name, parameters):
    client.live_events.begin_stop(resource_group_name, account_name, live_event_name, parameters)
    
stop_live_event(resource_group_name, account_name, live_event_name, parameters=parameters)
#</StopLiveEvent>

#<UpdateLiveEvent>
# Set the properties that you want to set for the live event
# For this sample, we want to change the live event streaming protocol to fragmented MP4.
live_event = LiveEvent(
    location=media_account.location,
    input=LiveEventInput(
        streaming_protocol=LiveEventInputProtocol.FRAGMENTED_MP4
    ),
    encoding=LiveEventEncoding(
        encoding_type=LiveEventEncodingType.PREMIUM1080_P,
        preset_name="default1080p"
    ),
    use_static_hostname=True,
    hostname_prefix=live_event_name,
    stream_options=[StreamOptionsFlag.DEFAULT]
)
# From SDK:
# begin_update(resource_group_name: str, account_name: str, live_event_name: str, parameters: azure.mgmt.media.models._models_py3.LiveEvent, **kwargs: Any) -> azure.core.polling._poller.LROPoller[azure.mgmt.media.models._models_py3.LiveEvent]
def update_live_event(resource_group_name, account_name, live_event_name, parameters):
    client.live_events.begin_update(resource_group_name, account_name, live_event_name, parameters)
    
update_live_event(resource_group_name, account_name, live_event_name, parameters=live_event)
#</UpdateLiveEvent>

#<GetLiveEvent>
# From SDK:
# get(resource_group_name: str, account_name: str, live_event_name: str, **kwargs: Any) -> azure.mgmt.media.models._models_py3.LiveEvent
def get_live_event(resource_group_name, account_name, live_event_name):
    results = client.live_events.get(resource_group_name, account_name, live_event_name)
    # You can get any properties of live event. Here, we are printing the live event input.
    print(results.input)
    
get_live_event(resource_group_name, account_name, live_event_name)
#</GetLiveEvent>

#<ListLiveEvent>
# From SDK:
# list(resource_group_name: str, account_name: str, **kwargs: Any) -> Iterable[azure.mgmt.media.models._models_py3.LiveEventListResult]
def list_live_event(resource_group_name, account_name):
    results = client.live_events.list(resource_group_name, account_name)
    # For this sample, we are printing the list of all live events in the current Media Services Account
    for liveevent in results:
        print(liveevent.name)
        
list_live_event(resource_group_name, account_name)
#</ListLiveEvent>

#<DeleteLiveEvent>
# From SDK:
# begin_delete(resource_group_name: str, account_name: str, live_event_name: str, **kwargs: Any) -> azure.core.polling._poller.LROPoller[None]
def delete_live_event(resource_group_name, account_name, live_event_name):
    client.live_events.begin_delete(resource_group_name, account_name, live_event_name)

delete_live_event(resource_group_name, account_name, live_event_name)
#</DeleteLiveEvent>
