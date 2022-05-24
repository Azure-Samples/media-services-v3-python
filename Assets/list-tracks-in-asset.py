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
  StreamingLocator
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

# The file you want to upload.  For this example, the file is placed under Media folder.
# The file ignite.mp4 has been provided for you. 
source_file_location = os.chdir("../../Media/")
source_file = "ignite.mp4"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "list-tracks"

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

transform_name = 'ContentAwareEncoding'

# Create a Encoding transform
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
my_transform.description="Transform with List Tracks in Assets"
my_transform.outputs = [transform_output]

print(f"Creating transform {transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=transform_name,
  parameters=my_transform
)

print(f"{transform_name} created (or updated if it existed already). ")

job_name = 'ListTracksInAsset'+ uniqueness
print(f"Creating custom encoding job {job_name}")
files = (source_file)

# Create Job Input and Ouput Asset
input = JobInputAsset(asset_name=in_asset_name)
outputs = JobOutputAsset(asset_name=out_asset_name)

# Create job object and then create a transform job
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

# List all of the tracks available on this asset
for track in client.tracks.list(resource_group, account_name, out_asset_name):
    print(f"Track Name: {track.name} \t Track: {track.track}")

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
  
  if locator.name:
    streaming_endpoint = client.streaming_endpoints.get(
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
      print("The streaming links: ")
      for path in paths.streaming_paths:
        for formatPath in path.paths:
          manifest_path = "https://" + streaming_endpoint.host_name + formatPath
          print(manifest_path)
          print(f"Click to playback in AMP player: http://ampdemo.azureedge.net/?url={manifest_path}")
      print("The output asset for streaming via HLS or DASH was successful!")
    else:
        raise Exception("Locator was not created or Locator.name is undefined")
