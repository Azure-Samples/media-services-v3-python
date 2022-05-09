# This sample demonstrates how to create an very simple Transform to use for submitting any custom Job into.
# Creating a very basic transform in this fashion allows you to treat the AMS v3 API more like the legacy v2 API where 
# transforms were not required, and you could submit any number of custom jobs to the same endpoint. 
# In the new v3 API, the default workflow is to create a transform "template" that holds a unique queue of jobs just for that
# specific "recipe" of custom or pre-defined encoding. 

# In this sample, we show you how to create the blank empty Transform, and then submit a couple unique custom jobs to it,
# overriding the blank empty Transform. 

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
  H265Video,
  H265Layer,
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

# The file you want to upload.  For this example, the file is placed under Media folder.
# The file ignite.mp4 has been provided for you. 
source_file_location = os.chdir("../../Media/")
source_file = "ignite.mp4"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "emptyTransform"

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
in_container = 'asset-' + in_asset.asset_id

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

transform_name = 'EmptyTransform'

# Create a new Standard encoding Transform for H264
print(f"Creating empty, blank, Standard Encoding transform named: {transform_name}")

# In this sample, we create the simplest of Transforms allowed by the API to later submit custom jobs against.
# Even though we define a single layer H264 preset here, we are going to override it later with a custom job level preset.
# This allows you to treat this single Transform queue like the legacy v2 API, which only supported a single Job queue type.
# In v3 API, the typical workflow that you will see in other samples is to create a transform "recipe" and submit jobs to it
# that are all of the same type of output. 
# Some customers need the flexibility to submit custom Jobs. 

# First we create an mostly empty TransformOutput with a very basic H264 preset that we override later.
# If a Job were submitted to this base Transform, the output would be a single MP4 video track at 1 Mbps. 

# For this snippet, we are using 'BuiltInStandardEncoderPreset'
# Create a new Content Aware Encoding Preset using the Preset Configuration
transform_output = TransformOutput(
  preset=StandardEncoderPreset(
    codecs=[
        H264Video(layers=[H264Layer(bitrate=1000000)])      # Units are in bits per second and not kbps or Mbps - 1 Mbps or 1,000 kbps
    ],
    # Specify the format for the output files - one for video+audio, and another for the thumbnails
    formats=[
      # Mux the H.264 video and AAC audio into MP4 files, using basename, label, bitrate and extension macros
      # Note that since you have multiple H264Layers defined above, you have to use a macro that produces unique names per H264Layer
      # Either {Label} or {Bitrate} should suffice
      Mp4Format(filename_pattern="Video-{Basename}-{Label}-{Bitrate}{Extension}")
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
my_transform.description="An empty transform to be used for submitting custom jobs against"
my_transform.outputs = [transform_output]

print(f"Creating transform {transform_name}")

transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=transform_name,
  parameters=my_transform)

print(f"{transform_name} created (or updated if it existed already). ")

job_name = 'MyEncodingSpriteThumbnailJob'+ uniqueness
print(f"Creating EncodingSpriteThumbnail job {job_name}")
files = (source_file)

input = JobInputAsset(asset_name=in_asset_name)

print("Creating the output Asset (container) to encode the content into...")
outputs = JobOutputAsset(asset_name=out_asset_name)

print(f"Creating a new custom preset override and submitting the job to the empty transform {transform_name} job queue...")

# Create a new Preset Override to define a custom standard encoding preset
standard_preset_h264 = StandardEncoderPreset(
    codecs=[
        H264Video(
            # Next, add a H264Video for the video encoding
            key_frame_interval=timedelta(seconds=2),
            complexity=H264Complexity.SPEED,
            layers=[
                H264Layer(
                    bitrate=3600000,  # Units are in bits per second and not kbps or Mbps - 3.6 Mbps or 3,600 kbps
                    width="1280",
                    height="720",
                    label="HD-3600kbps"   # This label is used to modify the file name in the output formats
                )
            ]
        ), 
        AacAudio(
            # Add an AAC Audio Layer for the audio encoding
            channels=2,
            sampling_rate=48000,
            bitrate=128000,
            profile=AacAudioProfile.AAC_LC
        )
    ],
    formats=[
        Mp4Format(filename_pattern="Video-{Basename}-{Label}-{Bitrate}{Extension}")
    ]
)

outputs = JobOutputAsset(asset_name=out_asset_name, preset_override=standard_preset_h264)

the_job = Job(input=input,outputs=[outputs])

# Submit the H264 encoding custom job, passing in the preset override defined above.
job: Job = client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)

# Next, we will create another preset override that uses HEVC instead and submit it against the same simple transform
# Create a new Preset Override to define a custom standard encoding preset
standard_preset_HEVC = StandardEncoderPreset(
    codecs=[
        H265Video(
            # Next, add a H265Video for the video encoding
            key_frame_interval=timedelta(seconds=2),
            complexity=H264Complexity.SPEED,
            layers=[
                H265Layer(
                    bitrate=1800000, # Units are in bits per second and not kbps or Mbps - 3.6 Mbps or 3,600 kbps
                    max_bitrate=1800000,
                    width="1280",
                    height="720",
                    b_frames=4,
                    label="HD-1800kbps" # This label is used to modify the file name in the output formats
                )
            ]
        ), 
        AacAudio(
            # Add an AAC audio layer for the audio encoding
            channels=2,
            sampling_rate=48000,
            bitrate=128000,
            profile=AacAudioProfile.AAC_LC    
        )
    ],
    formats=[
        Mp4Format(filename_pattern="Video-{Basename}-{Label}-{Bitrate}{Extension}")
    ]
)

# Let's update some names to re-use for the HEVC job we want to submit
job_name_hevc = job_name + '_HEVC'
out_asset_name_hevc = out_asset_name + '_HEVC'

# Set the attributes of the output Asset for HEVC
out_alternate_id_hevc = out_alternate_id + '_HEVC'
out_description_hevc = out_description + '_HEVC'

# Let's create a new output asset
print("Creating a new output Asset (container) to endcode the content into...")
out_asset_hevc = Asset(alternate_id=out_alternate_id_hevc, description=out_description_hevc)

out_asset_hevc = client.assets.create_or_update(resource_group, account_name, out_asset_name_hevc, out_asset_hevc)

outputs_hevc = JobOutputAsset(asset_name=out_asset_name_hevc, preset_override=standard_preset_HEVC)

the_job2 = Job(input=input, outputs=[outputs_hevc])

# Submit the next HEVC custom job, passing in the preset override defined above.
job: Job = client.jobs.create(resource_group, account_name, transform_name, job_name_hevc, parameters=the_job2)

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

job_state2 = client.jobs.get(resource_group, account_name, transform_name, job_name_hevc)
# Second job check
print("Second job check")
print(job_state2.state)

# Check the state of the job every 10 seconds. Adjust time_in_seconds = <how often you want to check for job state>
def countdown(t):
    while t: 
        mins, secs = divmod(t, 60) 
        timer = '{:02d}:{:02d}'.format(mins, secs) 
        print(timer, end="\r") 
        time.sleep(1) 
        t -= 1
    job_current2 = client.jobs.get(resource_group, account_name, transform_name, job_name_hevc)
    if(job_current2.state == "Finished"):
      print(job_current2.state)
      # TODO: Download the output file using blob storage SDK
      return
    if(job_current2.state == "Error"):
      print(job_current2.state)
      # TODO: Provide Error details from Job through API
      return
    else:
      print(job_current2.state)
      countdown(int(time_in_seconds))

time_in_seconds = 10
countdown(int(time_in_seconds))
