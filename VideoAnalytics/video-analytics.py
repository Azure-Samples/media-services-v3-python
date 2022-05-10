from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.storage.blob import BlobServiceClient
from azure.mgmt.media.models import (
  Asset,
  Transform,
  TransformOutput,
  AudioAnalyzerPreset,
  AudioAnalysisMode,
  VideoAnalyzerPreset,
  Job,
  JobInputAsset,
  JobOutputAsset,
  OnErrorType,
  Priority
)
import os

#Timer for checking job progress
import time

# Get environment variables
load_dotenv()

# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
default_credential = DefaultAzureCredential()

# Get the environment variables SUBSCRIPTIONID, RESOURCEGROUP and ACCOUNTNAME
subscription_id = os.getenv('SUBSCRIPTIONID')
resource_group = os.getenv('RESOURCEGROUP')
account_name = os.getenv('ACCOUNTNAME')

# The file you want to upload.  For this example, put the file in the same folder as this script. 
# The file ignite.mp4 has been provided for you. 
source_file = "ignite.mp4"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "analyze-videoaudio"

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

# Create an ouput asset object
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

audio_transform_name = 'AudioAnalyzerTransform'
video_transform_name = 'VideoAnalyzerTransform'

# # For this snippet, we are using 'BuiltInStandardEncoderPreset'
audio_transform_output = TransformOutput(
  preset=AudioAnalyzerPreset(
    audio_language="en-US",   # Be sure to modify this to your desired language code in BCP-47 format.
    # Set the language to British English - see see https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#speech-to-text 
    
    # There are two modes available, Basic and Standard
    # Basic : This mode performs speech-to-text transcription and generation of a VTT subtitle/caption file.
    #         The output of this mode includes an Insights JSON file including only the keywords, transcription, and timing information.
    #         Automatic language detection and speaker diarization are not included in this mode.
    # Standard : Performs all operations included in the Basic mode, additionally performing language detection and speaker diarization.
    mode=AudioAnalysisMode.BASIC    # Change this to Standard if you would like to use the more advanced audio analyzer
  ),
  # What should we do with the job if there is an error?
  on_error=OnErrorType.STOP_PROCESSING_JOB,
  # What is the relative priority of this job to others? Normal, high or low?
  relative_priority=Priority.NORMAL
)

# Create a new Video Analyzer Transform Preset using the preset configuration
video_transform_output = TransformOutput(
  preset=VideoAnalyzerPreset(
    audio_language="en-US",   # Be sure to modify this to your desired language code in BCP-47 format
    insights_to_extract="AllInsights",    # Video Analyzer can also run in Video only mode.
    mode="Standard",    # Video analyzer can also process audio in basic or standard mode when using All Insights
    experimental_options={  # Optional settings for preview or experimental features
      # "SpeechProfanityFilterMode="None" " # Disables the speech-to-text profanity filtering
    }
  )
)

# Ensure that you have customized transforms for the AudioAnalyzer. This is really a one time setup operation.
print("Creating Audio Analyzer transform...")

# Adding transform details
my_transform = Transform()
my_transform.description="A simple Audio Analyzer Transform"
my_transform.outputs = [audio_transform_output]

print(f"Creating transform {audio_transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=audio_transform_name,
  parameters=my_transform)

print(f"{audio_transform_name} created (or updated if it existed already). ")

# Ensure that you have customized transforms for the VideoAnalyzer. This is really a one time setup operation.
print("Creating Video Analyzer transform...")

# Adding transform details
my_transform2 = Transform()
my_transform2.description="A simple Video Analyzer Transform"
my_transform2.outputs = [video_transform_output]

print(f"Creating transform {video_transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=video_transform_name,
  parameters=my_transform2
)

print(f"{video_transform_name} created (or updated if it existed already). ")

audio_job_name = 'AudioAnalyticsJob'+ uniqueness
video_job_name = 'VideoAnalyticsJob'+ uniqueness

# Choose which of the analyzer job name you would like to Use
# For the audio analytics job, use audio_job_name
# For the video analytics job, use video_job_name
analysis_job_name = audio_job_name
print(f"Creating Analytics job {analysis_job_name}")
files = (source_file)

# Create Job Input and Job Output Asset
input = JobInputAsset(asset_name=in_asset_name)
outputs = JobOutputAsset(asset_name=out_asset_name)

# Create a job object
the_job = Job(input=input,outputs=[outputs])

# Choose which of the analyzer Transform names you would like to use here by changing the name of the Transform to be used
# For the basic audio analyzer - pass in the audio_transform_name
# For the video analyzer - change this code to pass in the video_transform_name
analysis_transform_name = audio_transform_name

# Create a transform job
job: Job = client.jobs.create(resource_group, account_name, analysis_transform_name, analysis_job_name, parameters=the_job)

# Check Job State
job_state = client.jobs.get(resource_group, account_name, analysis_transform_name, analysis_job_name)
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
    job_current = client.jobs.get(resource_group, account_name, analysis_transform_name, analysis_job_name)
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
