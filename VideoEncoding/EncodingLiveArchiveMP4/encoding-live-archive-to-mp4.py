# This sample shows how to copy a section of a live event archive (output from the LiveOutput) to an MP4 file for use in downstream applications
# It is also useful to use this technique to get a file that you can submit to YouTube, Facebook, or other social platforms.
# The output from this can also be submitted to the Video Indexer service, which currently does not support ingest of AMS live archives
#
# The key concept to know in this sample is the VideoTrackDescriptor that allows you to extract a specific bitrate from a live archive ABR set.

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (
  Asset,
  Transform,
  TransformOutput,
  StandardEncoderPreset,
  CopyAudio,
  CopyVideo,
  Mp4Format,
  SelectVideoTrackByAttribute,
  TrackAttribute,
  AttributeFilter,
  FromAllInputFile,
  Job,
  JobInputAsset,
  JobOutputAsset,
  OnErrorType,
  Priority
  )
import os

#Timer for checking job progress
import time

#Get environment variables
load_dotenv()

# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
default_credential = DefaultAzureCredential()

# Get the environment variables SUBSCRIPTIONID, RESOURCEGROUP and ACCOUNTNAME
subscription_id = os.getenv('SUBSCRIPTIONID')
resource_group = os.getenv('RESOURCEGROUP')
account_name = os.getenv('ACCOUNTNAME')

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "encode_copy_live"

# Set the attributes of the input Asset using the random number
in_asset_name = 'inputassetName' + uniqueness
in_alternate_id = 'inputALTid' + uniqueness
in_description = 'inputdescription' + uniqueness

# Create an Asset object
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
in_asset = Asset(alternate_id=in_alternate_id, description=in_description)

# Set this to the name of the Asset used in your LiveOutput. This would be the archived live event Asset name. 
input_archive_name = 'archiveAsset-2793'

# Set the attributes of the output Asset using the random number
out_asset_name = 'outputassetName' + uniqueness
out_alternate_id = 'outputALTid' + uniqueness
out_description = 'outputdescription' + uniqueness

# Create Output Asset object
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

transform_name = 'CopyLiveArchiveToMP4'

# Create a new Standard encoding Transform for H264
print(f"Creating Standard Encoding transform named: {transform_name}")

# For this snippet, we are using 'StandardEncoderPreset'
transform_output = TransformOutput(
  preset=StandardEncoderPreset(
    codecs=[
      CopyAudio(),
      CopyVideo()
    ],
    filters={},
    # Specify the format for the output files - one for video+audio, and another for the thumbnails
    formats=[
      # Mux the H.264 video and AAC audio into MP4 files, using basename, label, bitrate and extension macros
      # Note that since you have multiple H264Layers defined above, you have to use a macro that produces unique names per H264Layer
      # Either {Label} or {Bitrate} should suffice
      Mp4Format(
        filename_pattern="Video-{Basename}-{Label}-{Bitrate}{Extension}"
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
my_transform.description="Built in preset using the Saas Copy Codec preset. This copies the source audio and video to an MP4 file"
my_transform.outputs = [transform_output]

print(f"Creating transform {transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=transform_name,
  parameters=my_transform)

print(f"{transform_name} created (or updated if it existed already). ")

job_name = 'MyEncodingLiveArchiveToMP4Job'+ uniqueness
print(f"Creating encoding job {job_name}")
# files = (source_file)

# Use this to select the top bitrate from the live archive asset
# The filter property allows you to select the "Top" bitrate which would be the 
# highest bitrate provided by the live encoder.
video_track_selection = SelectVideoTrackByAttribute(
  attribute=TrackAttribute.BITRATE,
  filter=AttributeFilter.TOP    # Use this to select the top bitrate in this ABR asset for the job
)

# Create Job Input and Job Output Asset
input = JobInputAsset(
  asset_name=input_archive_name,
  input_definitions=[
    FromAllInputFile(
      included_tracks=[
        video_track_selection   # Pass in the SelectVideoTrackByAttribute object created above to select only the top video.
      ]
    )
  ]
)
outputs = JobOutputAsset(asset_name=out_asset_name)

# Create Job object and then create Transform Job
the_job = Job(input=input,outputs=[outputs])
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
