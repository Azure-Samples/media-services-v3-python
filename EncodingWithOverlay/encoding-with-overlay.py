from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.mgmt.media.models import (
  Asset,
  Transform,
  TransformOutput,
  ## classes for custom transform
  StandardEncoderPreset,
  Filters,
  VideoOverlay,
  AacAudio,
  H264Video,
  H264Layer,
  Mp4Format,
  ## 
  Job,
  JobInputs,
  JobInputAsset,
  JobOutputAsset)
import os, uuid, sys

#Timer for checking job progress
import time

#This is only necessary for the random number generation
import random

# Set and get environment variables
# Open sample.env, edit the values there and save the file as .env
# (Not all of the values may be used in this sample code, but the .env file is reusable.)
# Use config to use the .env file.
print("Getting .env values")
default_value = "<Fill out the .env>"
account_name = os.getenv('ACCOUNTNAME',default_value)
resource_group_name = os.getenv('RESOURCEGROUP',default_value)
subscription_id = os.getenv('SUBSCRIPTIONID',default_value)

#### STORAGE ####
# Values from .env and the blob url
# For this sample you will use the storage account connection string to create and access assets
storage_account_connection = os.getenv('STORAGEACCOUNTCONNECTION',default_value)

# Get the default Azure credential from the environment variables AADCLIENTID and AADSECRET
default_credential = DefaultAzureCredential()

# The video file & overlay logo image file(.png etc.)you want to upload.  For this example, put the file in the same folder as this script. 
# The file sample_video_globe.mp4 & cloud.png has been provided for you. 
source_file = "sample_video_globe.mp4"
source_file_logo = "cloud.png"

# Generate a random number that will be added to the naming of things so that you don't have to keep doing this during testing.
thisRandom = random.randint(0,9999)

# Set the attributes of the input Video Asset using the random number
in_asset_name = 'inputassetName' + str(thisRandom)
in_alternate_id = 'inputALTid' + str(thisRandom)
in_description = 'inputdescription' + str(thisRandom)

#++ Set the attributes of the input logo Asset using the random number
in_asset_name_logo = 'inputlogoassetName' + str(thisRandom)
in_alternate_id_logo = 'inputlogoALTid' + str(thisRandom)
in_description_logo = 'inputlogodescription' + str(thisRandom)
#++ Set label name to add to the job input asset of overlay image 
in_label_name_logo = "logo"

# Create an Asset object for the video & logo
# From the SDK
# Asset(*, alternate_id: str = None, description: str = None, container: str = None, storage_account_name: str = None, **kwargs) -> None
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
input_asset = Asset(alternate_id=in_alternate_id,description=in_description)
input_asset_logo = Asset(alternate_id=in_alternate_id_logo,description=in_description_logo)

# Set the attributes of the output Asset using the random number
out_asset_name = 'outputassetName' + str(thisRandom)
out_alternate_id = 'outputALTid' + str(thisRandom)
out_description = 'outputdescription' + str(thisRandom)

# Create an Asset object for the output
# From the SDK
# Asset(*, alternate_id: str = None, description: str = None, container: str = None, storage_account_name: str = None, **kwargs) -> None
output_asset = Asset(alternate_id=out_alternate_id,description=out_description)

# The AMS Client
print("Creating AMS client")
# From SDK
# AzureMediaServices(credentials, subscription_id, base_url=None)
client = AzureMediaServices(default_credential, subscription_id)

# Create an input video Asset
print("Creating input asset " + in_asset_name)
# From SDK
# create_or_update(resource_group_name, account_name, asset_name, parameters, custom_headers=None, raw=False, **operation_config)
inputAsset = client.assets.create_or_update(resource_group_name, account_name, in_asset_name, input_asset)
#++ Create an input logoAsset
print("Creating input asset " + in_asset_name_logo)
inputAssetLogo = client.assets.create_or_update(resource_group_name, account_name, in_asset_name_logo, input_asset_logo)

# An AMS asset is a container with a specfic id that has "asset-" prepended to the GUID.
# So, you need to create the asset id to identify it as the container
# where Storage is to upload the video (as a block blob)
in_container = 'asset-' + inputAsset.asset_id

in_container_logo = 'asset-' + inputAssetLogo.asset_id

# create an output Asset
print("Creating output asset " + out_asset_name)
# From SDK
# create_or_update(resource_group_name, account_name, asset_name, parameters, custom_headers=None, raw=False, **operation_config)
outputAsset = client.assets.create_or_update(resource_group_name, account_name, out_asset_name, output_asset)

### Use the Storage SDK to upload the video ###
print("Uploading the video file " + source_file)

blob_service_client = BlobServiceClient.from_connection_string(storage_account_connection)

# From SDK
# get_blob_client(container, blob, snapshot=None)
blob_client = blob_service_client.get_blob_client(in_container,source_file)
# Upload the video to storage as a block blob
with open(source_file, "rb") as data:
  # From SDK
  # upload_blob(data, blob_type=<BlobType.BlockBlob: 'BlockBlob'>, length=None, metadata=None, **kwargs)
    blob_client.upload_blob(data, blob_type="BlockBlob")

###++ Use the Storage SDK to upload the logo image ###
print("Uploading the logo file " + source_file_logo)
# From SDK
# BlobServiceClient(account_url, credential=None, **kwargs)
#blob_service_client = BlobServiceClient(account_url=storage_blob_url, credential=storage_account_key)
# From SDK
# get_blob_client(container, blob, snapshot=None)
blob_client = blob_service_client.get_blob_client(in_container_logo,source_file_logo)
# Upload the video to storage as a block blob
with open(source_file_logo, "rb") as data:
  # From SDK
  # upload_blob(data, blob_type=<BlobType.BlockBlob: 'BlockBlob'>, length=None, metadata=None, **kwargs)
    blob_client.upload_blob(data, blob_type="BlockBlob")



### Create a custom Transform ###
transform_name='MyTransformWithOverlay' + str(thisRandom)
# From SDK
# TransformOutput(*, preset, on_error=None, relative_priority=None, **kwargs) -> None
##++ Custom Transform with Overlay image
transform_output = TransformOutput(
    preset=StandardEncoderPreset(
        filters=Filters(overlays=[VideoOverlay(input_label=in_label_name_logo)]),
        codecs=[AacAudio(),H264Video(key_frame_interval=datetime.timedelta(seconds=2),layers=[H264Layer(bitrate=1000000,width="1140",height="640",profile="Baseline")])],
        formats=[Mp4Format(filename_pattern="{Basename}_{Bitrate}{Extension}")]
    )    
)

print("Creating transform " + transform_name)
# From SDK
# Create_or_update(resource_group_name, account_name, transform_name, outputs, description=None, custom_headers=None, raw=False, **operation_config)
transform = client.transforms.create_or_update(resource_group_name=resource_group_name,account_name=account_name,transform_name=transform_name,outputs=[transform_output])

### Create a Job ###
job_name = 'MyOvarlayEncodingJob'+ str(thisRandom)
print("Creating overlay encoding job " + job_name)
files = (source_file)
# From SDK
# JobInputAsset(*, asset_name: str, label: str = None, files=None, **kwargs) -> None
input = JobInputAsset(asset_name=in_asset_name)
#++ pass label name for overlay input asset
overlay = JobInputAsset(asset_name=in_asset_name_logo, label=in_label_name_logo)

# From SDK
# JobOutputAsset(*, asset_name: str, **kwargs) -> None
outputs = JobOutputAsset(asset_name=out_asset_name)
# From SDK
# Job(*, input, outputs, description: str = None, priority=None, correlation_data=None, **kwargs) -> None
#++ create JobInputs object and add video asset and log asset to it
theJob = Job(input=JobInputs(inputs=[input,overlay]), outputs=[outputs])
# From SDK
# Create(resource_group_name, account_name, transform_name, job_name, parameters, custom_headers=None, raw=False, **operation_config)
job: Job = client.jobs.create(resource_group_name,account_name,transform_name,job_name,parameters=theJob)

### Check the progress of the job ### 
# From SDK
# get(resource_group_name, account_name, transform_name, job_name, custom_headers=None, raw=False, **operation_config)
job_state = client.jobs.get(resource_group_name,account_name,transform_name,job_name)
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
    job_state = client.jobs.get(resource_group_name,account_name,transform_name,job_name)
    if(job_state.state != "Finished"):
      print(job_state.state)
      countdown(int(time_in_seconds))
    else:
      print(job_state.state)
time_in_seconds = 10
countdown(int(time_in_seconds))
