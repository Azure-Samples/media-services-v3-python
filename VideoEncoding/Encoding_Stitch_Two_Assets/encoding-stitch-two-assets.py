from datetime import timedelta
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.storage.blob import BlobServiceClient
from azure.mgmt.media.models import (
  Asset,
  Transform,
  TransformOutput,
  StandardEncoderPreset,
  AacAudio,
  AacAudioProfile,
  H264Video,
  H264Complexity,
  H264Layer,
  Mp4Format,
  JobInputSequence,
  AbsoluteClipTime,
  Job,
  JobInputAsset,
  JobOutputAsset,
  OnErrorType,
  Priority,
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

# The file you want to upload.  For this example, put the file in the same folder as this script. 
# The file ignite.mp4 has been provided for you. 
# Also, the Azure_Bumper.mp4 has been provided for you.
source_file = "ignite.mp4"
bumper_file = "Azure_Bumper.mp4"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "stitchTwoAssets"

# Set the attributes of the input Asset using the random number
in_asset_name = 'inputassetName' + uniqueness
in_alternate_id = 'inputALTid' + uniqueness
in_description = 'inputdescription' + uniqueness

# Create an Asset object
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
input_asset = Asset(alternate_id=in_alternate_id, description=in_description)

# Set the attributes of the bumper input Asset using the random number
bumper_asset_name = 'bumperassetName' + uniqueness
bumper_alternate_id = 'bumperALTid' + uniqueness
bumper_description = 'bumperdescription' + uniqueness

# Create a Bumper Asset object
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
bumper_asset = Asset(alternate_id=bumper_alternate_id, description=bumper_description)

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

# Create an input Asset
print(f"Creating input asset {bumper_asset_name}")
bumperAsset = client.assets.create_or_update(RESOURCE_GROUP, ACCOUNT_NAME, bumper_asset_name, bumper_asset)

# # An AMS asset is a container with a specific id that has "asset-" prepended to the GUID.
# # So, you need to create the asset id to identify it as the container
# # where Storage is to upload the video (as a block blob)
bumper_container = 'asset-' + bumperAsset.asset_id

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
  
### Use the Storage SDK to upload the bumper file ###
print(f"Uploading the file {bumper_file}")

blob_service_client = BlobServiceClient.from_connection_string(os.getenv('STORAGEACCOUNTCONNECTION'))
blob_client = blob_service_client.get_blob_client(bumper_container, bumper_file)
working_dir = os.getcwd()
print(f"Current working directory: {working_dir}")
upload_file_path = os.path.join(working_dir, bumper_file)

# WARNING: Depending on where you are launching the sample from, the path here could be off, and not include the BasicEncoding folder. 
# Adjust the path as needed depending on how you are launching this python sample file. 

# Upload the bumper video to storage as a block blob
with open(upload_file_path, "rb") as data:
  blob_client.upload_blob(data)

transform_name = 'StitchTwoAssets'

# Create a new Standard encoding Transform for H264
print(f"Creating Standard Encoding transform named: {transform_name}")

# For this snippet, we are using 'StandardEncoderPreset'
# Create a new Content Aware Encoding Preset using the Preset Configuration
transform_output = TransformOutput(
  preset = StandardEncoderPreset(
    codecs = [AacAudio(channels = 2, sampling_rate = 48000, bitrate = 128000, profile = AacAudioProfile.AAC_LC),
              H264Video(key_frame_interval = timedelta(seconds = 2), complexity = H264Complexity.BALANCED, layers = [H264Layer(bitrate=3600000, width="1280", height="720", label="HD-3600kbps")]),
    ],
    # Specify the format for the output files - one for video+audio, and another for the thumbnails
    formats = [
      # Mux the H.264 video and AAC audio into MP4 files, using basename, label, bitrate and extension macros
      # Note that since you have multiple H264Layers defined above, you have to use a macro that produces unique names per H264Layer
      # Either {Label} or {Bitrate} should suffice
      Mp4Format(filename_pattern = "Video-{Basename}-{Label}-{Bitrate}{Extension}")
    ]
  ),
  # What should we do with the job if there is an error?
  on_error=OnErrorType.STOP_PROCESSING_JOB,
  # What is the relative priority of this job to others? Normal, high or low?
  relative_priority=Priority.NORMAL
)

print("Creating encoding transform...")

# Adding transform details
myTransform = Transform()
myTransform.description="Stitches together two assets"
myTransform.outputs = [transform_output]

print(f"Creating transform {transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=RESOURCE_GROUP,
  account_name=ACCOUNT_NAME,
  transform_name=transform_name,
  parameters = myTransform)

print(f"{transform_name} created (or updated if it existed already). ")

job_name = 'MyEncodingStitchTwoAssetsJob'+ uniqueness
print(f"Creating EncodingStitchTwoAssets job {job_name}")
files = (source_file)

# Create a new Asset and upload the 1st specified local video file into it. This is our video "bumper" to stitch to the front.
main_input = JobInputAsset(asset_name=in_asset_name, files=source_file)   # This creates and uploads the main video file

# Create a second Asset and upload the 2nd specified local videeo file into it.
bumper_input = JobInputAsset(asset_name=bumper_asset_name, files=bumper_file)     # This creates and uploads the second video file.

print(f"The main asset is: {in_asset_name}")
print(f"The bumper asset is: {bumper_asset_name}")

# Create a Job Input Sequence with the two assets to stitch together
# In this sample, we will stitch a bumper into the main video asset at the head, 6 seconds, and at the tail. We end the main video at 12s total.
# TIMELINE :   | Bumper | Main video -----> 6 s | Bumper | Main Video 6s -----------> 12s | Bumper |s
# You can extend this sample to stitch any number of assets together and adjust the time offsets to create custom edits
jobInputSequence = JobInputSequence(
  inputs=[
    # Start with the bumper video file
    JobInputAsset(
      asset_name=bumper_asset_name,
      files=[bumper_file],
      start=AbsoluteClipTime(time=timedelta(seconds=0)),
      label="bumper"
    ),
    # Cut to 6 seconds of the main video
    JobInputAsset(
      asset_name=in_asset_name,
      files=[source_file],
      start=AbsoluteClipTime(time=timedelta(seconds=0)),
      end=AbsoluteClipTime(time=timedelta(seconds=6)),
      label="main"
    ),
    # Mid-roll the bumper again just to annoy people...
    JobInputAsset(
      asset_name=bumper_asset_name,
      files=[bumper_file],
      start=AbsoluteClipTime(time=timedelta(seconds=0)),
      label="bumper"
    ),
    # Go back to main video for 6 seconds
    JobInputAsset(
      asset_name=in_asset_name,
      files=[source_file],
      start=AbsoluteClipTime(time=timedelta(seconds=6)),
      end=AbsoluteClipTime(time=timedelta(seconds=12)),
      label="main"
    ),
    # Post-roll the bumper again just to annoy people even more, as though this was Hulu with ads and their inventory
    JobInputAsset(
      asset_name=bumper_asset_name,
      files=[bumper_file],
      start=AbsoluteClipTime(time=timedelta(seconds=0)),
      label="bumper"
    )
  ]
)

# Create Job Output Asset
outputs = JobOutputAsset(asset_name=out_asset_name)

# Create Job object and then create Transform Job
theJob = Job(input=jobInputSequence, outputs=[outputs])
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
