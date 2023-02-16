# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# Azure Media Services Live Streaming Sample for Python
# This sample demonstrates how to enable Low Latency HLS (LL-HLS) streaming with encoding

# This sample assumes that you will use OBS Studio to broadcast RTMP
# to the ingest endpoint. Please install OBS Studio first.
# Use the following settings in OBS:
#   Encoder: NVIDIA NVENC (if avail) or x264
#   Rate control : CDR
#   Bitrate: 2500 kbps (or something reasonable for your laptop)
#   Keyframe Interval : 2s, or 1s for low latency
#   Preset: Low-latency Quality or Performance (NVENC) or "veryfast" using x264
#   Profile: high
#   GPU: 0 (Auto)
#   Max B-frames: 2

# The workflow for the sample and for the recommended use of the Live API:
# 1) Create the client for AMS using AAD service principal or managed ID
# 2) Set up your IP restriction allow objects for ingest and preview
# 3) Configure the Live Event object with your settings. Choose pass-through
#   or encoding channel type and size (720p or 1080p)
# 4) Create the Live Event without starting it
# 5) Create an Asset to be used for recording the live stream into
# 6) Create a Live Output, which acts as the "recorder" to record into the
#    Asset (which is like the tape in the recorder).
# 7) Start the Live Event - this can take a little bit.
# 8) Get the preview endpoint to monitor in a player for DASH or HLS.
# 9) Get the ingest RTMP endpoint URL for use in OBS Studio.
#    Set up OBS studio and start the broadcast.  Monitor the stream in
#    your DASH or HLS player of choice.
# 10) Create a new Streaming Locator on the recording Asset object from step 5.
# 11) Get the URLs for the HLS and DASH manifest to share with your audience
#    or CMS system. This can also be created earlier after step 5 if desired.

import asyncio
from datetime import timedelta
import time
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.media.aio import AzureMediaServices
from azure.mgmt.media.models import (
    Asset,
    IPRange,
    IPAccessControl,
    LiveEvent,
    LiveEventInputAccessControl,
    LiveEventPreviewAccessControl,
    LiveEventPreview,
    LiveEventInput,
    LiveOutput,
    LiveEventEncoding,
    LiveEventEncodingType,
    LiveEventInputProtocol,
    StreamOptionsFlag,
    Hls,
    StreamingLocator
)
import os
import random

# Get the environment variables
load_dotenv()

# This sample uses the default Azure Credential object, which relies on the environment variable settings.

default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

# Get the environment variables
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
resource_group = os.getenv('AZURE_RESOURCE_GROUP')
account_name = os.getenv('AZURE_MEDIA_SERVICES_ACCOUNT_NAME')

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = random.randint(0,9999)
prefix = "basic-pass-live-event"
live_event_name = f'{prefix}-{uniqueness}'     # WARNING: Be careful not to leak live events using this sample!
asset_name = f'{prefix}-archive-asset-{uniqueness}'
live_output_name = f'{prefix}-live-output-{uniqueness}'
streaming_locator_name = f'{prefix}-live-stream-locator-{uniqueness}'
streaming_endpoint_name = 'default'     # Change this to your specific streaming endpoint name if not using "default"
manifest_name = "output"

print("Starting the Live Streaming sample for Azure Media Services")
# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)

# Creating the LiveEvent - the primary object for live streaming in AMS.
# See the overview - https://docs.microsoft.com/azure/media-services/latest/live-streaming-overview

# Create the LiveEvent

# Understand the concepts of what a live event and a live output is in AMS first!
# Read the following - https://docs.microsoft.com/azure/media-services/latest/live-events-outputs-concept
# 1) Understand the billing implications for the various states
# 2) Understand the different live event types, pass-through and encoding
# 3) Understand how to use long-running async operations
# 4) Understand the available Standby mode and how it differs from the Running Mode.
# 5) Understand the differences between a LiveOutput and the Asset that it records to.  They are two different concepts.
#    A live output can be considered as the "tape recorder" and the Asset is the tape that is inserted into it for recording.
# 6) Understand the advanced options such as low latency, and live transcription/captioning support.
#    Live Transcription - https://docs.microsoft.com/en-us/azure/media-services/latest/live-transcription
#    Low Latency - https://docs.microsoft.com/en-us/azure/media-services/latest/live-event-latency

# When broadcasting to a live event, please use one of the verified on-premises live streaminf encoders.
# While operating this tutorial, it is recommended to start out using OBS Studio before moving to another encoder.

# Note: When creating a LiveEvent, you can specify allowed IP addresses in one of the following formats:
#       IPV4 address with 4 numbers
#       CIDR address range

allow_all_input_range=IPRange(name="AllowAll", address="0.0.0.0", subnet_prefix_length=0)

# Create the LiveEvent input IP access control object
# This will control the IP that the encoder is running on and restrict access to only that encoder IP range.
# re-use the same range here for the sample, but in production, you can lock this down to the IP range for your on-premises
# live encoder, laptop, or device that is sending the live stream
live_event_input_access=LiveEventInputAccessControl(ip=IPAccessControl(allow=[allow_all_input_range]))


# Create the LiveEvent Preview IP access control object.
# This will restrict which clients can view the preview endpoint
# re-se the same range here for the sample, but in production, you can lock this to the IPs of your
# devices that would be monitoring the live preview.
live_event_preview=LiveEventPreview(access_control=LiveEventPreviewAccessControl(ip=IPAccessControl(allow=[allow_all_input_range])))

# To get the same ingest URL for the same LiveEvent name every single time...
# 1. Set useStaticHostname to true so you have inget like:
#       rtmps://liveevent-hevc12-eventgridmediaservice-usw22.channel.media.azure.net:2935/live/522f9b27dd2d4b26aeb9ef8ab96c5c77
# 2. Set accessToken to a desired GUID string (with or without hyphen)

# See REST API documentation for the details on each setting value
# https://docs.microsoft.com/rest/api/media/liveevents/create

live_event_create=LiveEvent(
    # NOTE: Make sure that your live stream is located in the same region as your Media Services account.
    # Otherwise, a Resource Not Found error for your AMS account will be thrown.
    location="West US",       # For the sample, we are using location: West US 2
    description="Sample 720P Encoding Live Event from Python SDK sample",
    # Set useStaticHostname to true to make the ingest and preview URL host name the same.
    # This can slow things down a bit.
    use_static_hostname=True,
    # hostname_prefix= "somethingstatic",     # When using Static host name true, you can control the host prefix name here if desired
    # 1) Set up the input settings for the Live event...
    input=LiveEventInput(
        streaming_protocol=LiveEventInputProtocol.RTMP,     # Options are RTMP or Smooth Streaming ingest format.
        access_control=live_event_input_access,     # controls the IP restriction for the source header
        # key_frame_interval_duration = timedelta(seconds = 2),       # Set this to match the ingest encoder's settings. This should not be used for encoding channels
        access_token='9eb1f703b149417c8448771867f48501'       # Use this value when you want to make sure the ingest URL is static and always the same. If omitted, the service will generate a random GUID values.
    ),

    # 2) Set the live event to use pass-through or cloud encoding modes...
    encoding=LiveEventEncoding(
        # Set this to Basic pass-through, Standard pass-through, Standard or Premium1080P to use the cloud live encoder.
        # See https://go.microsoft.com/fwlink/?linkid=2095101 for more information
        # Otherwise, leave as "None" to use pass-through mode
        encoding_type=LiveEventEncodingType.PASSTHROUGH_BASIC,
        # OPTIONS for encoding type you can use:
        # encoding_type=LiveEventEncodingType.PassthroughBasic, # Basic pass-through mode - the cheapest option!
        # encoding_type=LiveEventEncodingType.PassthroughStandard, # also known as standard pass-through mode (formerly "none")
        # encoding_type=LiveEventEncodingType.Premium1080p, # live transcoding up to 1080P 30fps with adaptive bitrate set
        # encoding_type=LiveEventEncodingType.Standard, # use live transcoding in the cloud for 720P 30fps with adaptive bitrate set

        # OPTIONS using live cloud encoding type:
        # key_frame_interval=timedelta(seconds = 2), # If this value is not set for an encoding live event, the fragment duration defaults to 2 seconds. The value cannot be set for pass-through live events.

        # For Low Latency HLS Live streaming, there are two new custom presets available:
        # "720p-3-Layer": For use with a Standard 720P encoding_type live event
        # {"ElementaryStreams":[{"Type":"Video","BitRate":2500000,"Width":1280,"Height":720},{"Type":"Video","BitRate":1000000,"Width":960,"Height":540},{"Type":"Video","BitRate":400000,"Width":640,"Height":360}]}"
        # "1080p-4-Layer":  For use with a Premium1080p encoding_type live event
        # {"ElementaryStreams":[{"Type":"Video","BitRate":4500000,"Width":1920,"Height":1080},{"Type":"Video","BitRate":2200000,"Width":1280,"Height":720},{"Type":"Video","BitRate":1000000,"Width":960,"Height":540},{"Type":"Video","BitRate":400000,"Width":640,"Height":360}]}

        # preset_name=None, # only used for custom defined presets.
        # stretch_mode= None # can be used to determine stretch on encoder mode
    ),

    # 3) Set up the Preview endpoint for monitoring based on the settings above we already set.
    preview=live_event_preview,

    # 4) Set up more advanced options on the live event. Low Latency is the most common one.
    # To enable Apple's Low Latency HLS (LL-HLS) streaming, you must use "LOW_LATENCY_V2" stream option
    stream_options=[StreamOptionsFlag.LOW_LATENCY]

    #5) Optionally, enable live transcriptions if desired.
    # WARNING : This is extra cost ($$$), so please check pricing before enabling. Transcriptions are not supported on PassthroughBasic.
    #           switch this sample to use encodingType: "PassthroughStandard" first before un-commenting the transcriptions object below.

    # transcriptions = LiveEventTranscription(
    #     input_track_selection = [],     # Choose which track to transcribe on the source input.
    #     # The value should be in BCP-47 format (e.g: 'en-US'). See https://go.microsoft.com/fwlink/?linkid=2133742
    #     language = 'en-US',
    #     output_transcription_track = LiveEventOutputTranscriptionTrack(
    #         track_name = 'English'      # Set the name you want to appear in the output manifest
    #     )
    # )
)

print("Creating the LiveEvent, please be patient as this can take time to complete async.")
print("Live Event creation is an async operation in Azure and timing can depend on resources available.")
print()

# When autostart is set to true, the Live Event will be started after creation.
# That means, the billing starts as soon as the Live Event starts running.
# You must explicitly call Stop on the Live Event resource to halt further billing.
# The following operation can sometimes take awhile. Be patient.
# On optional workflow is to first call allocate() instead of create.
# https://docs.microsoft.com/en-us/rest/api/media/liveevents/allocate
# This allows you to allocate the resources and place the live event into a "Standby" mode until
# you are ready to transition to "Running". This is useful when you want to pool resources in a warm "Standby" state at a reduced cost.
# The transition from Standby to "Running" is much faster than cold creation to "Running" using the autostart property.
# Returns a long running operation polling object that can be used to poll until completion.

async def main():
    async with client:
        client_live = await client.live_events.begin_create(resource_group_name=resource_group, account_name=account_name, live_event_name=live_event_name, parameters=live_event_create, auto_start=True)
        time_start = time.perf_counter()
        time_end = time.perf_counter()
        execution_time = (time_end - time_start)
        if client_live:
            print(f"Live Event Created - long running operation complete! Name: {live_event_name}")
            print(f"Execution time to create LiveEvent: {execution_time:.2f}seconds")
            print()
            poller = client_live
            print(await poller.result())
        else:
            raise ValueError('Live Event creation failed!')

        # Create an Asset for the LiveOutput to use. Think of this as the "tape" that will be recorded to.
        # The asset entity points to a folder/container in your Azure Storage account.
        print(f"Creating an asset named: {asset_name}")
        print()

        out_alternate_id = f'outputALTid-{uniqueness}'
        out_description = f'outputdescription-{uniqueness}'

        # Create an output asset object
        out_asset = Asset(alternate_id=out_alternate_id, description=out_description)

        # Create an output asset
        output_asset = await client.assets.create_or_update(resource_group, account_name, asset_name, out_asset)

        if output_asset:
            # print output asset name
            print(f"The output asset name is: {output_asset.name}")
            print()
        else:
            raise ValueError('Output Asset creation failed!')

        # Create the Live Output - think of this as the "tape recorder for the live event".
        # Live outputs are optional, but are required if you want to archive the event to storage,
        # use the asset for on-demand playback later, or if you want to enable cloud DVR time-shifting.
        # We will use the asset created above for the "tape" to record to.
        manifest_name = "output"

        # See the REST API for details on each of the settings on Live Output
        # https://docs.microsoft.com/rest/api/media/liveoutputs/create

        print(f"Creating a live output named: {live_output_name}")
        print()

        if output_asset:
            time_start = time.perf_counter()
            live_output_create = LiveOutput(
                description="Optional description when using more than one live output",
                asset_name=output_asset.name,
                manifest_name=manifest_name,      # The HLS and DASH manifest file name. This is recommended to set if you want a deterministic manifest path up front.
                archive_window_length=timedelta(hours=1),     # Sets an one hour time-shift DVR window. Uses ISO 8601 format string.
                hls=Hls(
                    fragments_per_ts_segment=1        # Advanced setting when using HLS TS output only.
                )
            )

            print(f"live_output_create object is {live_output_create}")
            print()

            # Create and await the live output
            live_output_await = await client.live_outputs.begin_create(resource_group_name=resource_group, account_name=account_name, live_event_name=live_event_name, live_output_name=live_output_name, parameters=live_output_create)
            if live_output_await:
                print(f"Live Output created: {live_output_name}")
                poller = live_output_await
                print(await poller.result())
                time_end = time.perf_counter()
                execution_time = time_end - time_start
                print(f"Execution time to create LiveEvent: {execution_time:.2f}seconds")
                print()
            else:
                raise Exception("Live Output creation failed!")

        # Refresh the LiveEvent object's settings after starting it...
        live_event = await client.live_events.get(resource_group, account_name, live_event_name)

        # Get the RTMP ingest URL to configure in OBS Studio
        # The endpoints is a collection of RTMP primary and secondary, and RTMPS primary and secondary URLs.
        # to get the primary secure RTMPS, it is usually going to be index 3, but you could add a loop here to confirm...
        if live_event.input.endpoints:
            ingest_url = live_event.input.endpoints[0].url

            print("The RTMP ingest URL to enter into OBS Studio is:")
            print(f"RTMP ingest: {ingest_url}")
            print("Make sure to enter a Stream Key into the OBS studio settings. It can be any value or you can repeat the accessToken used in the ingest URL path.")
            print()

        if live_event.preview.endpoints:
            # Use the preview_endpoint to preview and verify
            # that the input from the encoder is actually being received
            # The preview endpoint URL also support the addition of various format strings for HLS (format=m3u8-cmaf) and DASH (format=mpd-time-cmaf) for example.
            # The default manifest is Smooth.
            preview_endpoint = live_event.preview.endpoints[0].url

            print(f"The preview url is: {preview_endpoint}")
            print()
            print("Open the live preview in your browser and use any DASH and HLS player to monitor the preview playback.")
            print(f"https://ampdemo.azureedge.net/?url={preview_endpoint}(format=mpd-time-cmaf)&heuristicprofile=lowlatency")
            print("You will need to refresh the player page SEVERAL times until enough data has arrived to allow for manifest creation.")
            print("In a production player, the player can inspect the manifest to see if it contains enough content for the player to load and auto reload.")
            print()


        print("Start the live stream now, sending the input to the ingest url and verify that it is arriving with the preview url.")
        print("IMPORTANT TIP!: Make CERTAIN that the video is flowing to the Preview URL before continuing!")

        # Create the Streaming Locator URL for playback of the contents in the Live Output recoding

        print(f"Creating a streaming locator named: {streaming_locator_name}")
        print()
        streaming_locator = StreamingLocator(asset_name=asset_name, streaming_policy_name="Predefined_ClearStreamingOnly")

        locator = await client.streaming_locators.create(
            resource_group_name=resource_group,
            account_name=account_name,
            streaming_locator_name=streaming_locator_name,
            parameters=streaming_locator
        )

        # Get the default streaming endpoint on the account
        streaming_endpoint = await client.streaming_endpoints.get(
            resource_group_name=resource_group,
            account_name=account_name,
            streaming_endpoint_name=streaming_endpoint_name
        )

        if streaming_endpoint.resource_state != "Running":
            print(f"Streaming endpoint is stopped. Starting the endpoint named {streaming_endpoint_name}...")
            poller = await client.streaming_endpoints.begin_start(resource_group, account_name, streaming_endpoint_name)
            client_streaming_begin = await poller.result()
            print("Streaming Endpoint started.")
            if not client_streaming_begin:
                print("Streaming Endpoint was already started.")

        # Get the URL to stream the Output
        print("The streaming URLs to stream the live output from a client player")
        print()

        host_name = streaming_endpoint.host_name
        scheme = 'https'

        # If you wish to get the streaming manifest ahead of time, make sure to set the manifest name in the LiveOutput as done above.
        # This allows you to have a deterministic manifest path. <streaming endpoint hostname>/<streaming locator ID>/manifestName.ism/manifest(<format string>)

        # Building the paths statically. Which is highly recommended when you want to share the stream manifests
        # to a player application or CMS system ahead of the live event.
        hls_format = "format=m3u8-cmaf"
        dash_format = "format=mpd-time-cmaf"

        manifest_base = f"{scheme}://{host_name}/{locator.streaming_locator_id}/{manifest_name}.ism/manifest"

        hls_manifest = f'{manifest_base}({hls_format})'
        print(f"The HLS (MP4) manifest URL is: {hls_manifest}")
        print("Open the following URL to playback the live stream in an HLS compliant player (HLS.js, Shaka, ExoPlayer) or directly in an iOS device")
        print({hls_manifest})
        print()

        dash_manifest = f'{manifest_base}({dash_format})'
        print(f"The DASH manifest URL is: {dash_manifest}")
        print("Open the following URL to playback the live stream from the LiveOutput in the Azure Media Player")
        print(f"https://ampdemo.azureedge.net/?url={dash_manifest}&heuristicprofile=lowlatency")
        print()

    # closing media client
    print('Closing media client')
    await client.close()

    # closing credential client
    print('Closing credential client')
    await default_credential.close()

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
