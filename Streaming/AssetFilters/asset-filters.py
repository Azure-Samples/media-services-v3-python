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

# Get the environment variables SUBSCRIPTIONID, RESOURCEGROUP and ACCOUNTNAME
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
resource_group = os.getenv('AZURE_RESOURCE_GROUP')
account_name = os.getenv('AZURE_MEDIA_SERVICES_ACCOUNT_NAME')

# The file you want to upload.  For this example, put the file in the same folder as this script.
# The file ignite.mp4 has been provided for you.
source_file = "ignite.mp4"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "streamAssetFilters-" + str(random.randint(0,9999))

# Change this to your specific streaming endpoint name if not using "default"
streaming_endpoint_name = "default"

# Set the attributes of the input Asset using the random number
in_asset_name = 'inputassetName' + uniqueness
in_alternate_id = 'inputALTid' + uniqueness
in_description = 'inputdescription' + uniqueness

# Create an Asset object
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
in_asset = Asset(alternate_id=in_alternate_id, description=in_description)

# Set the attributes of the output Asset using the random number
out_asset_name = 'outputassetName' + uniqueness
out_alternate_id = 'outputALTid' + uniqueness
out_description = 'outputdescription' + uniqueness

# Create an output asset object
out_asset = Asset(alternate_id=out_alternate_id, description=out_description)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)

# Create an input Asset
print(f"Creating input asset {in_asset_name}")
input_asset = client.assets.create_or_update(resource_group, account_name, in_asset_name, in_asset)

# An AMS asset is a container with a specific id that has "asset-" prepended to the GUID.
# So, you need to create the asset id to identify it as the container
# where Storage is to upload the video (as a block blob)
in_container = 'asset-' + input_asset.asset_id

# create an output Asset
print(f"Creating output asset {out_asset_name}")
output_asset = client.assets.create_or_update(resource_group, account_name, out_asset_name, out_asset)

### Use the Storage SDK to upload the video ###
print(f"Uploading the file {source_file}")

blob_service_client = BlobServiceClient.from_connection_string(os.getenv('STORAGEACCOUNTCONNECTION'))
blob_client = blob_service_client.get_blob_client(in_container, source_file)
working_dir = os.getcwd()
print(f"Current working directory: {working_dir}")
upload_file_path = os.path.join(working_dir, source_file)

# WARNING: Depending on where you are launching the sample from, the path here could be off, and not include the BasicEncoding folder.
# Adjust the path as needed depending on how you are launching this python sample file.

# Upload the video to storage as a block blob
with open(upload_file_path, "rb") as data:
  blob_client.upload_blob(data)

transform_name = 'ContentAwareEncodingAssetFilters'

# Create a new Standard encoding Transform for Built-in Copy Codec
print(f"Creating Encoding transform named: {transform_name}")
# For this snippet, we are using 'BuiltInStandardEncoderPreset'
transform_output = TransformOutput(
  preset=BuiltInStandardEncoderPreset(
    preset_name="ContentAwareEncoding"
  ),
  # What should we do with the job if there is an error?
  on_error=OnErrorType.STOP_PROCESSING_JOB,
  # What is the relative priority of this job to others? Normal, high or low?
  relative_priority=Priority.NORMAL
)

print("Creating encoding transform...")

# Adding transform details
my_transform = Transform()
my_transform.description="Transform with Asset filters"
my_transform.outputs = [transform_output]

print(f"Creating transform {transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=transform_name,
  parameters=my_transform)

print(f"{transform_name} created (or updated if it existed already). ")

job_name = 'ContentAwareEncodingAssetFilters'+ uniqueness
print(f"Creating custom encoding job {job_name}")
files = (source_file)

# Create Job Input and Ouput Assets
input = JobInputAsset(asset_name=in_asset_name)
outputs = JobOutputAsset(asset_name=out_asset_name)

# Create the job object and then create transform job
the_job = Job(input=input, outputs=[outputs])
job: Job = client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)

# Check job state
job_state = client.jobs.get(resource_group, account_name, transform_name, job_name)
# First check
print("First job check")
print(job_state.state)

# Check the state of the job every 10 seconds. Adjust time_in_seconds = <how often you want to check for job state>
def countdown(t):
  while t:
    mins, secs = divmod(t, 60)
    timer = '{:02d}:{:02d}'.format(mins, secs)
    print(timer, end="\r")
    time.sleep(1)
    t -= 1
  job_current = client.jobs.get(resource_group, account_name, transform_name, job_name)
  if(job_current.state == "Finished"):
    print(job_current.state)
    # TODO: Download the output file using blob storage SDK
    return
  if(job_current.state == "Error"):
    print(job_current.state)
    # TODO: Provide Error details from Job through API
    return
  else:
    print(job_current.state)
    countdown(int(time_in_seconds))

time_in_seconds = 10
countdown(int(time_in_seconds))

print(f"Creating locator for streaming...")
# Publish the output asset for streaming via HLS or DASH
locator_name = f"locator-{uniqueness}"
if output_asset:
  streaming_locator = StreamingLocator(asset_name=out_asset_name, streaming_policy_name="Predefined_ClearStreamingOnly")
  locator = client.streaming_locators.create(
    resource_group_name=resource_group,
    account_name=account_name,
    streaming_locator_name=locator_name,
    parameters=streaming_locator
  )

  if locator:
    print(f"The streaming locator {locator_name} was successfully created!")
  else:
    raise Exception(f"Error while creating streaming locator {locator_name}")

  # Create the Asset filters
  print("Creating an asset filter...")
  asset_filter_name = 'filter1'

  # Create the asset filter
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

  if asset_filter:
    print(f"The asset filter ({asset_filter_name}) was successfully created.")
    print()
  else:
    raise ValueError("There was an issue creating the asset filter.")

  if locator.name:
    hls_format = "format=m3u8-cmaf"
    dash_format = "format=mpd-time-cmaf"

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
