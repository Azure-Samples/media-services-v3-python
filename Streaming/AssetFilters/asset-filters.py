# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# This script assumes that you already have assets created.
# If you haven't created any, try one of the encoding samples first,
# but don't delete the assets.  Then, come back to this script.

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.storage.blob import BlobServiceClient
from azure.mgmt.media.models import (
  Asset,
  Transform,
  TransformOutput,
  BuiltInStandardEncoderPreset,
  Job,
  JobInputAsset,
  JobOutputAsset,
  OnErrorType,
  Priority,
  StreamingLocator,
  AssetFilter,
  PresentationTimeRange
)
import os
import random

#Timer for checking job progress
import time

#Get environment variables
load_dotenv()


default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

# Get the environment variables
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
resource_group = os.getenv('AZURE_RESOURCE_GROUP')
account_name = os.getenv('AZURE_MEDIA_SERVICES_ACCOUNT_NAME')

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = random.randint(0,9999)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)

out_asset_name = "encodeH264-output-3215"
#out_asset_name = "enter the name of the output asset you used during encoding"

print(f"Creating locator for streaming...")
# Publish the output asset for streaming via HLS or DASH
locator_name = f"locator-{uniqueness}"

streaming_locator = StreamingLocator(asset_name=out_asset_name, streaming_policy_name="Predefined_ClearStreamingOnly")

try:
  locator = client.streaming_locators.create(
    resource_group_name=resource_group,
    account_name=account_name,
    streaming_locator_name=locator_name,
    parameters=streaming_locator
  )
except Exception as e:
  print(e)

# Create the Asset filters
print("Creating an asset filter...")
asset_filter_name = 'filter1'

# Create the asset filter
try:
  asset_filter = client.asset_filters.create_or_update(
    resource_group_name=resource_group,
    account_name=account_name,
    asset_name=out_asset_name,
    filter_name=asset_filter_name,
    parameters=AssetFilter(
      # In this sample, we are going to filter the manifest by the time range of the presentation using the default timescale.
      # You can adjust these settings for your own needs. Not that you can also control output tracks, and quality levels with a filter.
      tracks=[],
      # start_timestamp = 100000000 and end_timestamp = 300000000 using the default timescale will generate
      # a play-list that contains fragments from between 10 seconds and 30 seconds of the VoD presentation.
      # If a fragment straddles the boundary, the entire fragment will be included in the manifest.
      presentation_time_range=PresentationTimeRange(start_timestamp=100000000, end_timestamp=300000000)
    )
  )
except Exception as e:
  print(e)

hls_format = "format=m3u8-cmaf"
dash_format = "format=mpd-time-cmaf"

streaming_endpoint_name = "default"

# This filename assumes that you used one of the encoding samples
# and this is the file you uploaded.
source_file = "ignite.mp4"

# Get the default streaming endpoint on the account
streaming_endpoint = client.streaming_endpoints.get(
  resource_group_name=resource_group,
  account_name=account_name,
  streaming_endpoint_name=streaming_endpoint_name
  )

if streaming_endpoint.resource_state != "Running":
  print(f"Streaming endpoint is stopped. Starting endpoint named {streaming_endpoint_name}")
  client.streaming_endpoints.begin_start(resource_group, account_name, streaming_endpoint_name)

  basename_tup = os.path.splitext(source_file)    # Extracting the filename and extension
  path_extension = basename_tup[1]   # Setting extension of the path
  manifest_name = os.path.basename(source_file).replace(path_extension, "")
  print(f"The manifest name is: {manifest_name}")
  manifest_base = f"https://{streaming_endpoint.host_name}/{locator.streaming_locator_id}/{manifest_name}.ism/mainfest"

  hls_manifest = ""
  if asset_filter_name is None:
    hls_manifest = f'{manifest_base}({hls_format})'
  else:
    hls_manifest = f'{manifest_base}({hls_format},filter={asset_filter_name})'

  print(f"The HLS (MP4) manifest URL is: {hls_manifest}")
  print("Open the following URL to playback the live stream in an HLS compliant player (HLS.js, Shaka, ExoPlayer) or directly in an iOS device")
  print({hls_manifest})
  print()

  dash_manifest = ""
  if asset_filter_name is None:
    dash_manifest = f'{manifest_base}({dash_format})'
  else:
    dash_manifest = f'{manifest_base}({dash_format},filter={asset_filter_name})'

  print(f"The DASH manifest URL is: {dash_manifest}")
  print("Open the following URL to playbackk the live stream from the LiveOutput in the Azure Media Player")
  print(f"https://ampdemo.azureedge.net/?url={dash_manifest}&heuristicprofile=lowlatency")
  print()
else:
  raise ValueError("Locator was not created or Locator name is undefined.")

# When you are done testing, remember to stop the streaming endpoint, or you will incur billing charges.
# client.streaming_endpoints.begin_stop(resource_group, account_name, streaming_endpoint_name)