# This sample shows how to use the built-in Copy codec preset that can take a source video file that is already encoded
# using H264 and AAC audio, and copy it into MP4 tracks that are ready to be streamed by the AMS service.
# In addition, this preset generates a fast proxy MP4 from the source video. 
# This is very helpful for scenarios where you want to make the uploaded MP4 asset available quickly for streaming, but also generate
# a low quality proxy version of the asset for quick preview, video thumbnails, or low bitrate delivery while your application logic
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
  StandardEncoderPreset,
  Job,
  JobInputAsset,
  JobOutputAsset,
  OnErrorType,
  Priority,
  StreamingLocator,
  CopyVideo,
  CopyAudio,
  JpgImage,
  Mp4Format,
  JpgFormat,
  JpgLayer
)
import os

#Timer for checking job progress
import time

#Get environment variables
load_dotenv()


default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

# Get the environment variables SUBSCRIPTIONID, RESOURCEGROUP and ACCOUNTNAME
subscription_id = os.getenv('SUBSCRIPTIONID')
resource_group = os.getenv('RESOURCEGROUP')
account_name = os.getenv('ACCOUNTNAME')

# The file you want to upload.  For this example, the file is placed under Media folder.
# The file ignite.mp4 has been provided for you. 
source_file_location = os.chdir("../../Media/")
source_file = "ignite.mp4"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "-encode-copycodec-sprite-proxy"

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
# Create an Output Asset object
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

transform_name = 'CopyCodecWithSpriteAndProxyCustom'

# Create a new Standard encoding Transform for Built-in Copy Codec
print(f"Creating Built-in Standard CopyCodec with Proxy Encoding transform named: {transform_name}")

# For this snippet, we are using 'BuiltInStandardEncoderPreset'
transform_output = [
  TransformOutput(
    preset=BuiltInStandardEncoderPreset(
      preset_name="SaasSourceAligned360pOnly"       # There are some undocumented magical presets in our toolbox that do fun stuff - this one is going to copy the codecs from the source and also generate a 360p proxy file.
      
      # Other magical presets to play around with, that might (or might not) work for your source video content...
      # "SaasCopyCodec" - this just copies the source video and audio into an MP4 ready for streaming.  The source has to be H264 and AAC with CBR encoding and no B frames typically.
      # "SaasProxyCopyCodec" - this copies the source video and audio into an MP4 ready for streaming and generates a proxy file.   The source has to be H264 and AAC with CBR encoding and no B frames typically.
      # "SaasSourceAligned360pOnly" - same as above, but generates a single 360P proxy layer that is aligned in GOP to the source file. Useful for "back filling" a proxy on a pre-encoded file uploaded.  
      # "SaasSourceAligned540pOnly"-  generates a single 540P proxy layer that is aligned in GOP to the source file. Useful for "back filling" a proxy on a pre-encoded file uploaded. 
      # "SaasSourceAligned540p" - generates an adaptive set of 540P and 360P that is aligned to the source file. used for "back filling" a pre-encoded or uploaded source file in an output asset for better streaming.
      # "SaasSourceAligned360p" - generates an adaptive set of 360P and 180P that is aligned to the source file. used for "back filling" a pre-encoded or uploaded source file in an output asset for better streaming.
    ),
    # What should we do with the job if there is an error?
    on_error=OnErrorType.STOP_PROCESSING_JOB,
    # What is the relative priority of this job to others? Normal, high or low?
    relative_priority=Priority.NORMAL
  ),
  TransformOutput(
    # uses the Standard Encoder Preset to generate copy the source audio and video to an output track, and generate a proxy and a sprite
    preset=StandardEncoderPreset(
      # CopyVideo is a custom copy codec - it copies the source video track directly to the output MP4 file
      # CopyAudio is a custom copy codec - it copies the audio track from the source to the ouput MP4 file
      # JpgImage - generates a set of thumbnails in one Jpg file (thumbnail sprite) 
      codecs=[CopyVideo(), CopyAudio(), JpgImage(start="0%", step="5%", range="100%", sprite_column=10, layers=[JpgLayer(width="20%", height="20%", quality=85)])],
      
      # Specify the format for the output files - one for video+audio, and another for the thumbnails
      # Mux the H.264 video and AAC audio into MP4 files, using basename, label, bitrate and extension macros
      # Note that since you have multiple H264Layers defined above, you have to use a macro that produces unique names per H264Layer
      # Either {Label} or {Bitrate} should suffice
      formats=[Mp4Format(filename_pattern="CopyCodec-{Basename}{Extension}"), JpgFormat(filename_pattern="sprite-{Basename}-{Index}{Extension}")]  
    ),
    # What should we do with the job if there is an error?
    on_error=OnErrorType.STOP_PROCESSING_JOB,
    # What is the relative priority of this job to others? Normal, high or low?
    relative_priority=Priority.NORMAL
  )
]

print("Creating encoding transform...")

# Adding transform details
my_transform = Transform()
my_transform.description="Built in preset using the Saas Copy Codec preset. This copies the source audio and video to an MP4 file."
my_transform.outputs = transform_output

print(f"Creating transform {transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=transform_name,
  parameters=my_transform)

print(f"{transform_name} created (or updated if it existed already). ")

job_name = 'CopyCodecWithSpriteAndProxyCustom'+ uniqueness
print(f"Creating Encoding-CopyCodecWithSpriteAndProxyCustom job {job_name}")
files = (source_file)

# Creating Job Input Asset
input = JobInputAsset(asset_name=in_asset_name)

# Since the above transform generates two Transform outputs, we need to define two Job output assets to push that content.
# In this case, we want both Transform outputs to go back into the output asset container.
outputs = [
  JobOutputAsset(asset_name=out_asset_name),
  JobOutputAsset(asset_name=out_asset_name)
]

# Create Job object and then create a Transform Job
the_job = Job(input=input,outputs=outputs, correlation_data={"myTenant": "myCustomTenantName", "myId": "1234"})
job: Job = client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)

# Check Job State
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

# Publish the output asset for streaming via HLS or DASH
locator_name = "CopyCodecWithSpriteAndProxyCustomLocator"
if output_asset:
  # Create StreamingLocator object
  streamingLocator = StreamingLocator(asset_name=out_asset_name, streaming_policy_name="Predefined_ClearStreamingOnly")
  # Create Streaming Locator
  locator = client.streaming_locators.create(
    resource_group_name=resource_group,
    account_name=account_name,
    streaming_locator_name=locator_name,
    parameters=streamingLocator
  )
  if locator.name:
    streamingEndpoint = client.streaming_endpoints.get(
      resource_group_name=resource_group,
      account_name=account_name,
      streaming_endpoint_name="default"
    )

    paths = client.streaming_locators.list_paths(
      resource_group_name=resource_group,
      account_name=account_name,
      streaming_locator_name=locator_name 
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
