# This sample shows how to use the built-in Copy codec preset that can take a source video file that is already encoded
# using H264 and AAC audio, and copy it into MP4 tracks that are ready to be streamed by the AMS service.
# In addition, this preset generates a fast proxy MP4 from the source video. 
# This is very helpful for scenarios where you want to make the uploaded MP4 asset available quickly for streaming, but also generate
# allow quality proxy version of the asset for quick preview, video thumbnails, or low bitrate delivery while your application logic
# decides if you need to backfill any more additional layers (540P, 360P, etc) to make the full adaptive bitrate set complete. 
# This strategy is commonly used by services like YouTube to make content appear to be "instantly" available, but slowly fill in the 
# quality levels for a more complete adaptive streaming experience. See the Encoding_BuiltIn_CopyCodec sample for a version that does not
# generate the additional proxy layer. 
# 
# This is useful for scenarios where you have complete control over the source asset, and can encode it in a way that is 
# consistent with streaming (2-6 second GOP length, Constant Bitrate CBR encoding, no or limited B frames).
# This preset should be capable of converting a source 1 hour video into a streaming MP4 format in under 1 minute, as it is not
# doing any encoding - just re-packaging the content into MP4 files. 
#
# NOTE: If the input has any B frames encoded, we occasionally can get the GOP boundaries that are off by 1 tick
#       which can cause some issues with adaptive switching.
#       This preset works up to 4K and 60fps content.   

from importlib.resources import path
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
)
import os

#Timer for checking job progress
import time

#Get environment variables
load_dotenv()

# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
default_credential = DefaultAzureCredential()

# Get the environment variables SUBSCRIPTIONID, RESOURCEGROUP and ACCOUNTNAME
SUBSCRIPTION_ID = os.getenv('SUBSCRIPTIONID')
RESOURCE_GROUP = os.getenv('RESOURCEGROUP')
ACCOUNT_NAME = os.getenv('ACCOUNTNAME')

# The file you want to upload.  For this example, the file is placed under Media folder.
# The file ignite.mp4 has been provided for you. 
source_file_location = os.chdir("../../Media/")
source_file = "ignite.mp4"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "-encode-builtin-copycodec-with-proxy"

# Set the attributes of the input Asset using the random number
in_asset_name = 'inputassetName' + uniqueness
in_alternate_id = 'inputALTid' + uniqueness
in_description = 'inputdescription' + uniqueness

# Create an Asset object
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
input_asset = Asset(alternate_id=in_alternate_id, description=in_description)

# Set the attributes of the output Asset using the random number
out_asset_name = 'outputassetName' + uniqueness
out_alternate_id = 'outputALTid' + uniqueness
out_description = 'outputdescription' + uniqueness

# Create an Output Asset object
output_asset = Asset(alternate_id=out_alternate_id, description=out_description)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, SUBSCRIPTION_ID)

# Create an input Asset
print(f"Creating input asset {in_asset_name}")
inputAsset = client.assets.create_or_update(RESOURCE_GROUP, ACCOUNT_NAME, in_asset_name, input_asset)

# An AMS asset is a container with a specific id that has "asset-" prepended to the GUID.
# So, you need to create the asset id to identify it as the container
# where Storage is to upload the video (as a block blob)
in_container = 'asset-' + inputAsset.asset_id

# create an output Asset
print(f"Creating output asset {out_asset_name}")
outputAsset = client.assets.create_or_update(RESOURCE_GROUP, ACCOUNT_NAME, out_asset_name, output_asset)

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

transform_name = 'CopyCodecWithProxy'

# Create a new Standard encoding Transform for Built-in Copy Codec
print(f"Creating Built-in Standard CopyCodec with Proxy Encoding transform named: {transform_name}")

# For this snippet, we are using 'BuiltInStandardEncoderPreset'
transform_output = TransformOutput(
  preset = BuiltInStandardEncoderPreset(
    # uses the built in SaaS copy codec preset, which copies source audio and video to MP4 tracks. 
    # This also generates a fast proxy. See notes at top of this file on constraints and use case.
    preset_name="saasProxyCopyCodec"   
  ),
  # What should we do with the job if there is an error?
  on_error=OnErrorType.STOP_PROCESSING_JOB,
  # What is the relative priority of this job to others? Normal, high or low?
  relative_priority=Priority.NORMAL
)

print("Creating encoding transform...")

# Adding transform details
myTransform = Transform()
myTransform.description="Built in preset using the Saas Copy Codec preset. This copies the source audio and video to an MP4 file."
myTransform.outputs = [transform_output]

print(f"Creating transform {transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=RESOURCE_GROUP,
  account_name=ACCOUNT_NAME,
  transform_name=transform_name,
  parameters = myTransform)

print(f"{transform_name} created (or updated if it existed already). ")

job_name = 'MyEncodingBuiltinCopyCodecWithProxy'+ uniqueness
print(f"Creating EncodingBuiltinCopyCodecWithProxy job {job_name}")
files = (source_file)

# Create Job Input and Output Asset
input = JobInputAsset(asset_name=in_asset_name)
outputs = JobOutputAsset(asset_name=out_asset_name)

# Create Job object and then create a Transform Job for the client
theJob = Job(input=input, outputs=[outputs])
job: Job = client.jobs.create(RESOURCE_GROUP, ACCOUNT_NAME, transform_name, job_name, parameters=theJob)

# Check Job State
job_state = client.jobs.get(RESOURCE_GROUP, ACCOUNT_NAME, transform_name, job_name)
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
  job_current = client.jobs.get(RESOURCE_GROUP, ACCOUNT_NAME, transform_name, job_name)
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

# Publish the output asset for streaming via HLS or DASH
locator_name = "CopyCodecWithProxyLocator"
if outputAsset is not None:
  # Create StreamingLocator object
  streamingLocator = StreamingLocator(asset_name=out_asset_name, streaming_policy_name="Predefined_ClearStreamingOnly")
  # Create Streaming Locator
  locator = client.streaming_locators.create(
    resource_group_name = RESOURCE_GROUP,
    account_name = ACCOUNT_NAME,
    streaming_locator_name= locator_name,
    parameters = streamingLocator
  )
  if locator.name is not None:
    streamingEndpoint = client.streaming_endpoints.get(
      resource_group_name = RESOURCE_GROUP,
      account_name = ACCOUNT_NAME,
      streaming_endpoint_name = "default"
    )
    
    paths = client.streaming_locators.list_paths(
      resource_group_name = RESOURCE_GROUP,
      account_name = ACCOUNT_NAME,
      streaming_locator_name = locator_name 
    )

    if paths.streaming_paths:
      print("The streaming links via HLS or DASH are: ")
      for path in paths.streaming_paths:
        for formatPath in path.paths:
          manifest_path = "https://" + streamingEndpoint.host_name + formatPath
          print(manifest_path)
          print(f"Click to playback in AMP player: http://ampdemo.azureedge.net/?url={manifest_path}")
      print("The output asset for streaming via HLS or DASH was successful!")
      print(f"The streaming locator name is {locator_name}")
    else:
      raise Exception("Locator was not created or Locator.name is undefined")
