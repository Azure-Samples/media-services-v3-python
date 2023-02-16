#<EncodingImports>
from datetime import timedelta
from msilib.schema import Media
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.storage.blob import BlobServiceClient
from azure.mgmt.media.models import (
  Asset,
  Transform,
  TransformOutput,
  StandardEncoderPreset,
  Job,
  JobInputAsset,
  JobOutputAsset,
  Filters,
  Rectangle,
  H264Layer,
  AacAudio,
  H264Video,
  H264Layer,
  H264Complexity,
  PngImage,
  Mp4Format,
  PngLayer,
  PngFormat,
  AacAudioProfile,
  OnErrorType,
  Priority
  )
import os
import random

#Timer for checking job progress
import time
#</EncodingImports>

#<ClientEnvironmentVariables>
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
uniqueness = random.randint(0,9999)

# Set the attributes of the input Asset using the random number
in_asset_name = f'inputassetName-{uniqueness}'
in_alternate_id = f'inputALTid-{uniqueness}'
in_description = f'inputdescription-{uniqueness}'

# Create an Asset object
# From the SDK
# Asset(*, alternate_id: str = None, description: str = None, container: str = None, storage_account_name: str = None, **kwargs) -> None
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
in_asset = Asset(alternate_id=in_alternate_id, description=in_description)

# Set the attributes of the output Asset using the random number
out_asset_name = f'outputassetName-{uniqueness}'
out_alternate_id = f'outputALTid-{uniqueness}'
out_description = f'outputdescription-{uniqueness}'
# From the SDK
# Asset(*, alternate_id: str = None, description: str = None, container: str = None, storage_account_name: str = None, **kwargs) -> None
out_asset = Asset(alternate_id=out_alternate_id,description=out_description)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)

# Create an input Asset
print(f"Creating input asset {in_asset_name}")
# From SDK
# create_or_update(resource_group_name, account_name, asset_name, parameters, custom_headers=None, raw=False, **operation_config)
input_asset = client.assets.create_or_update(resource_group, account_name, in_asset_name, in_asset)

# An AMS asset is a container with a specific id that has "asset-" prepended to the GUID.
# So, you need to create the asset id to identify it as the container
# where Storage is to upload the video (as a block blob)
in_container = 'asset-' + input_asset.asset_id

# create an output Asset
print(f"Creating output asset {out_asset_name}")
# From SDK
# create_or_update(resource_group_name, account_name, asset_name, parameters, custom_headers=None, raw=False, **operation_config)
output_asset = client.assets.create_or_update(resource_group, account_name, out_asset_name, out_asset)

### Use the Storage SDK to upload the video ###
print(f"Uploading the file {source_file}")

blob_service_client = BlobServiceClient.from_connection_string(os.getenv('STORAGEACCOUNTCONNECTION'))

# From SDK
# get_blob_client(container, blob, snapshot=None)
blob_client = blob_service_client.get_blob_client(in_container,source_file)
working_dir = os.getcwd()
print(f"Current working directory: {working_dir}")
upload_file_path = os.path.join(working_dir, source_file)

# WARNING: Depending on where you are launching the sample from, the path here could be off, and not include the BasicEncoding folder.
# Adjust the path as needed depending on how you are launching this python sample file.

# Upload the video to storage as a block blob
with open(upload_file_path, "rb") as data:
  # From SDK
  # upload_blob(data, blob_type=<BlobType.BlockBlob: 'BlockBlob'>, length=None, metadata=None, **kwargs)
  blob_client.upload_blob(data)


#<CreateTransform>
transform_name = 'Transform-Crop-Video'

# Create a new Standard encoding Transform for H264
print(f"Creating Standard Encoding transform named: {transform_name}")

# From SDK
# TransformOutput(*, preset, on_error=None, relative_priority=None, **kwargs) -> None
# For this snippet, we are using 'StandardEncoderPreset'

transform_output = TransformOutput(
  preset=StandardEncoderPreset(
    filters=Filters(
      crop=Rectangle(
        left="200",
        top="200",
        width="1280",
        height="720"
      )
    ),
    codecs=[
      AacAudio(
        # channels=2,
        # sampling_rate=48000,
        # bitrate=128000,
        # profile=AacAudioProfile.AAC_LC
      ),
      H264Video(
        layers=[
          H264Layer(
            bitrate=1000000,   # Units are in bits per second and not kbps or Mbps - 3.6Mbps or 3,600 kbps
            width="1280",
            height="720"
          )
        ],
      )
    ],
    # Specify the format for the output files - one for video+audio, and another for the thumbnails
    formats = [
      # Mux the H.264 video and AAC audio into MP4 files, using basename, label, bitrate and extension macros
      # Either {Label} or {Bitrate} should suffice
      Mp4Format(
        filename_pattern="Video-{Basename}-{Bitrate}{Extension}"
      )
    ]
  ),
  # What should we do with the job if there is an error?
  on_error=OnErrorType.STOP_PROCESSING_JOB,
  # What is the relative priority of this job to others? Normal, high or low?
  relative_priority=Priority.NORMAL
)

print("Creating encoding transform...")

# Adding transform details
my_transform = Transform()
my_transform.description="A simple custom H264 encoding transform with 3 MP4 bitrates"
my_transform.outputs = [transform_output]

print(f"Creating transform {transform_name}")
# From SDK
# Create_or_update(resource_group_name, account_name, transform_name, outputs, description=None, custom_headers=None, raw=False, **operation_config)
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=transform_name,
  parameters=my_transform)

print(f"{transform_name} created (or updated if it existed already). ")
#</CreateTransform>

#<CreateJob>
job_name = f'Transform-Crop-Video-Job-{uniqueness}'
print("Creating Encoding job " + job_name)
files = (source_file)

# From SDK
# JobInputAsset(*, asset_name: str, label: str = None, files=None, **kwargs) -> None
input = JobInputAsset(asset_name=in_asset_name)

# From SDK
# JobOutputAsset(*, asset_name: str, **kwargs) -> None
outputs = JobOutputAsset(asset_name=out_asset_name)

# From SDK
# Job(*, input, outputs, description: str = None, priority=None, correlation_data=None, **kwargs) -> None
the_job = Job(input=input, outputs=[outputs])

# From SDK
# Create(resource_group_name, account_name, transform_name, job_name, parameters, custom_headers=None, raw=False, **operation_config)
job: Job = client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)
#</CreateJob>

#<CheckJob>
# From SDK
# get(resource_group_name, account_name, transform_name, job_name, custom_headers=None, raw=False, **operation_config)
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
#</CheckJob>
