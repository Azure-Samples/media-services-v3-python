from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.storage.blob import BlobServiceClient
from azure.mgmt.media.models import (
  Asset,
  Transform,
  TransformOutput,
  SelectAudioTrackById,
  ChannelMapping,
  InputFile,
  StandardEncoderPreset,
  AacAudio,
  AacAudioProfile,
  Mp4Format,
  OutputFile,
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


default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

# Get the environment variables
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
resource_group = os.getenv('AZURE_RESOURCE_GROUP')
account_name = os.getenv('AZURE_MEDIA_SERVICES_ACCOUNT_NAME')

# The file you want to upload.  For this example, the file is placed under Media folder.
# Provide a sample file with 8 discrete audio tracks as layout is defined above.
source_file_location = os.chdir("../../Media/")
source_file = "surround-audio.mp4"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "encodeH264_multi_channel"

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

transform_name = 'Custom_AAC_MultiChannel_Surround'

# Create a new Standard encoding Transform for H264
print(f"Creating Standard Encoding transform named: {transform_name}" )

# The multi-channel audio file should contain a stereo pair on tracks 1 and 2, followed by multi channel 5.1 discrete tracks in the following layout
# 1. Left stereo
# 2. Right stereo
# 3. Left front surround
# 4. Right front surround
# 5. Center surround
# 6. Low frequency
# 7. Back left
# 8. Back right

# The channel mapping support is limited to only outputting a single AAC stereo track, followed by a 5.1 audio AAC track in this sample.

# The Transform we created outputs two tracks, the first track is mapped to the 2 stereo inputs followed by the 5.1 audio tracks.

# TrackDescriptor(SelectAudioTrackById(track_id = 0, channel_mapping = ChannelMapping.STEREO_LEFT))
# TypeError: TrackDescriptor.__init__() takes 1 positional argument but 2 were given
trackList = [
  SelectAudioTrackById(track_id=0, channel_mapping=ChannelMapping.STEREO_LEFT),
  SelectAudioTrackById(track_id=1, channel_mapping=ChannelMapping.STEREO_RIGHT),
  SelectAudioTrackById(track_id=2, channel_mapping=ChannelMapping.FRONT_LEFT),
  SelectAudioTrackById(track_id=3, channel_mapping=ChannelMapping.FRONT_RIGHT),
  SelectAudioTrackById(track_id=4, channel_mapping=ChannelMapping.CENTER),
  SelectAudioTrackById(track_id=5, channel_mapping=ChannelMapping.LOW_FREQUENCY_EFFECTS),
  SelectAudioTrackById(track_id=6, channel_mapping=ChannelMapping.BACK_LEFT),
  SelectAudioTrackById(track_id=7, channel_mapping=ChannelMapping.BACK_RIGHT)
]

# Create an input definition passing in the source file name and the list of included track mappings from that source file we made above.
inputDefinitions = [InputFile(filename=source_file, included_tracks=trackList)]

# For this snippet, we are using 'StandardEncoderPreset'
# Create a new Content Aware Encoding Preset using the Preset Configuration
transform_output = TransformOutput(
  preset=StandardEncoderPreset(
    codecs=[
      AacAudio(channels=2, sampling_rate=48000, bitrate=128000, profile=AacAudioProfile.AAC_LC, label="stereo"),
      AacAudio(channels=6, sampling_rate=48000, bitrate=320000, profile=AacAudioProfile.AAC_LC, label="surround")
    ],
    # Specify the format for the output files - one for AAC audio outputs to MP4
    formats=[
      # Mux the AAC audio into MP4 files, using basename, label, bitrate and extension macros
      # Note that since you have multiple AAC outputs defined above, you have to use a macro that produces unique names per AAC Layer
      # Either {Label} or {Bitrate} should suffice
      # By creating outputFiles and assigning the labels we can control which output tracks are muxed into the Mp4 files
      # If you choose to mux both the stereo and surround tracks into a single MP4 output, you can remove the outputFiles and remove the second MP4 format object.
      Mp4Format(filename_pattern="{Basename}-{Label}-{Bitrate}{Extension}", output_files=[OutputFile(labels=["stereo", "surround"])])
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
my_transform.description="A custom multi-channel audio encoding preset"
my_transform.outputs = [transform_output]

print(f"Creating transform {transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=transform_name,
  parameters=my_transform)

print(f"{transform_name} created (or updated if it existed already). ")

job_name = 'MyEncodingMultiChannnelAudioJob'+ uniqueness
print(f"Creating EncodingMultiChannelAudio job {job_name}")
files = (source_file)

# Create Job Input Asset and Job Input Asset with Track Definitions
input = JobInputAsset(asset_name=in_asset_name)
jobInputWithTrackDefinitions = JobInputAsset(asset_name = in_asset_name, input_definitions=inputDefinitions)

# Create Job Output Asset
outputs = JobOutputAsset(asset_name=out_asset_name)

# Create Job object and then create Transform Job
the_job = Job(input=jobInputWithTrackDefinitions, outputs=[outputs])
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
