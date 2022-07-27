from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.storage.blob import BlobServiceClient
from azure.mgmt.media.models import (
  Asset,
  PresetConfigurations,
  Complexity,
  InterleaveOutput,
  Transform,
  TransformOutput,
  BuiltInStandardEncoderPreset,
  Job,
  JobInputHttp,
  JobInputAsset,
  JobOutputAsset,
  OnErrorType,
  Priority
  )
import os
import random

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

# Sample Settings for Encoding Bulk Rmemote Storage Account
# A SAS URL to a remote blob storage account that you want to read files from
# Generate a Read/List SAS token URL in the portal under the storage accounts "shared access signature" menu
# Grant the allowed resource types : Service, Container, and Object
# Grant the allowed permissions: Read, List
remote_sas_url = os.getenv('REMOTESTORAGEACCOUNTSAS')

# This is the list of file extension filters we will scan the remote blob storage account SasURL for.
# The sample can loop through containers looking for assets with these extensions and then submit them to the Transform defined below in batches of 10.
FILE_EXTENSION_FILTERS = [".wmv", ".mov", ".mp4", ".mts"]

# If you want to optionally avoid copying specific output file types, you can set the postfix and extension to match in this array.
NO_COPY_EXTENSION_FILTERS = [".ism", ".ismc", ".mpi", "_metadata.json"]

# Change this flag to output all encoding to the SAS URL provided in the .env setting OUTPUTCONTAINERSAS
OUTPUT_TO_SAS = True
PRESERVE_HIERARCHY = True     # This will preserve the source file names and source folder hierarchy in the output container
PRESERVE_CONTAINER_PATH = True
DELETE_SOURCE_ASSETS = True

# If you set OUTPUT_TO_SAS to True,
OUTPUT_CONTAINER_SAS = os.getenv('OUTPUTCONTAINERSAS')
OUTPUT_CONTAINER_NAME = "output"
batch_counter = 0

# This is the batch size we chose for this sample - you can modify based on your own needs, but try not to exceed more than 50-100 in a batch unless you have contacted support first and let them know what region.
# Do that simply by opening a support ticket in the portal for increased quota and describe your scenario.
# If you need to process a bunch of stuff fast, use a busy region, like one of the major HERO regions (US East, US West, North and West Europe, etc.)
batch_job_size = 10     # This controls how many concurrent jobs we want to submit and wait to complete processing. . 
page_size = 500         # This controls how many blobs we read in the container per "page". 
job_input_queue = []

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "encodeH264-"+ str(random.randint(0,9999))

# # Set the attributes of the input Asset using the random number
# in_asset_name = 'inputassetName' + uniqueness
# in_alternate_id = 'inputALTid' + uniqueness
# in_description = 'inputdescription' + uniqueness

# # Create an Asset object
# # The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
# in_asset = Asset(alternate_id=in_alternate_id, description=in_description)

# # Set the attributes of the output Asset using the random number
# out_asset_name = 'outputassetName' + uniqueness
# out_alternate_id = 'outputALTid' + uniqueness
# out_description = 'outputdescription' + uniqueness

# # Create an Output Asset object
# out_asset = Asset(alternate_id=out_alternate_id, description=out_description)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)

# # Create an input Asset
# print(f"Creating input asset {in_asset_name}")
# input_asset = client.assets.create_or_update(resource_group, account_name, in_asset_name, in_asset)

# # An AMS asset is a container with a specific id that has "asset-" prepended to the GUID.
# # So, you need to create the asset id to identify it as the container
# # where Storage is to upload the video (as a block blob)
# in_container = 'asset-' + input_asset.asset_id

# # create an output Asset
# print(f"Creating output asset {out_asset_name}")
# output_asset = client.assets.create_or_update(resource_group, account_name, out_asset_name, out_asset)

transform_name = 'BatchRemoteH264ContentAware'

# Create a new Standard encoding Transform for H264
print(f"Creating Standard Encoding transform named: {transform_name}")

preset_config = PresetConfigurations(
  complexity=Complexity.QUALITY,
  # The output includes both audio and video.
  interleave_output=InterleaveOutput.INTERLEAVED_OUTPUT,
  # The key frame interval in seconds. Example: set as 2 to reduce the playback buffering for some players.
  key_frame_interval_in_seconds=2,
  # The maximum bitrate in bits per second (threshold for the top video layer). 
  # Example: set MaxBitrateBps as 6000000 to avoid producing very high bitrate outputs for contents with high complexity.
  max_bitrate_bps=6000000,
  # The minimum bitrate in bits per second (threshold for the bottom video layer).
  # Example: set MinBitrateBps as 200000 to have a bottom layer that covers users with low network bandwidth.
  min_bitrate_bps=200000,
  max_height=1080,
  # The minimum height of output video layers. 
  # Example: set MinHeight as 360 to avoid output layers of smaller resolutions like 180P.
  min_height=360,
  # The maximum number of output video layers.
  # Example: set MaxLayers as 4 to make sure at most 4 output layers are produced to control the overall cost of the encoding job.
  max_layers=1
)

# Create a new Content Aware Encoding Preset using the preset configuration
# For this snippet, we are using 'BuiltInStandardEncoderPreset'
transform_output = TransformOutput(
  preset=BuiltInStandardEncoderPreset(
    preset_name="ContentAwareEncoding",
    # Configurations can be used to control values used by the Content Aware Encoding Preset.
    configurations=preset_config
  ),
  # What should we do with the job if there is an error?
  on_error=OnErrorType.STOP_PROCESSING_JOB,
  # What is the relative priority of this job to others? Normal, high or low?
  relative_priority=Priority.NORMAL
)

print("Creating encoding transform...")

# Adding transform details
my_transform = Transform()
my_transform.description="H264 content aware encoding with configuration settings"
my_transform.outputs = [transform_output]

print(f"Creating transform {transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=transform_name,
  parameters=my_transform)

if transform:
  print(f"{transform_name} created (or updated if it existed already). ")
else:
  raise ValueError("There was an error creating the transform.")

# Now we are going to use SAS URL to the storage account to loop through all the containers and find video files
# with the extensions that we want to encode from. We can also use tags, or other metadata by modifying the code in the blobHelper library.

# First we need to create the blob service client with a SAS URL to the storage account. See settings for this at top of file.
blob_client = BlobServiceClient(remote_sas_url)
# Next we are going to get a list of all the containers in this storage account.
# For large accounts, you may need to modify this code to support pagination through the list of containers, as there is a default limit returned.
blob_containers = []
for container in blob_client.list_containers():
  blob_containers.append(container.name)
containers = blob_containers
print(f"The list of containers are: ")
container_count=1
for container in containers:
  print(f"{container_count}. Container: {container}")
  container_count +=1
  
# Next we will loop through each container looking for the file types we want to encode and then submit the encoding jobs using JobInputHTTP types
print("Found total of {} containers in the source location".format(len(containers)))

continuation_token=None
page_size=None
for container in containers:
  print("Scanning container: ", container)
  skip_ams_assets=True
  if skip_ams_assets or container == OUTPUT_CONTAINER_NAME:
    if container == OUTPUT_CONTAINER_NAME:
      print(f"Skipping over the defined output container: {OUTPUT_CONTAINER_NAME} to avoid re-encoding your outputs")

    if container.startswith("asset-"):
      print(f"Skipping over container {container} because it matches an AMS asset container with prefix 'asset-' and skip AMS assets is set to {skip_ams_assets}.")
      
  container_client = blob_client.get_container_client(container)
  blob_list=[]
  container_list=[]
  blob_matches=None
  blobs_list=None
  response=None
  
  blobs_list = container_client.list_blobs(include=["metadata"]) 
  if not blobs_list:
    raise Exception("Error in listing blobs within the container.")
  
  for blob in blobs_list:
    if blob.metadata:
      if blob.metadata.get("ams_encoded") == "true":
        print(f"Blob {blob.name} already encoded by AMS, skipping.")
        continue
    
    # if blob.items:
    #   if FILE_EXTENSION_FILTERS is not None:
    #     for element in FILE_EXTENSION_FILTERS:
    #       if element in blob.name:
    #         print(f"Found blob {blob.name} with extension: {element} in container: {container}")
    #         blob_list.append(blob)
    #   else:
    #     print(f"No blobs found in container: {container}")
    # else:
    #   print(f"No blob item found.")
    
    
    for element in FILE_EXTENSION_FILTERS:
      if element in blob.name:
        print(f"Found blob {blob.name} with extension: {element} in container: {container}")
        blob_list.append(blob)
        
    sas_url = blob_client.url
    sas_url_with_path = sas_url + container + blob.name
    job_input_queue.append(sas_url_with_path)
    print(f"SAS URL is: {sas_url}")
      
  # for element in FILE_EXTENSION_FILTERS:
  #   if element in blob.name:
  #     print(f"Found blob {blob.name} with extension: {element} in container: {container}")
  #     blob_list.append(blob)
  #     container_list.append(container)
  # break

  # print(f"The Job Input Queue is: [{job_input_queue}]")
  job_queue=[]
  
  # After the blobs are found in their respective containers, the programs shuts off itself.
  # The following stuff comes from a function located at:
  # https://github.com/Azure-Samples/media-services-v3-node-tutorials/blob/e466ecc333bb1bed2afe52c0954f93ff86b106f1/Common/Storage/blobStorage.ts#L44
  # Having a hard time understanding what is breaking up the program...
  # Node.js uses a URIBuilder which is not available for Python SDK
  # for blob in blobs_list:
  #   sas_url = blob_client.url
  #   sas_url_with_path = sas_url + container + blob.name
  #   job_input_queue.append(sas_url_with_path)
  #   print(f"SAS URL is: {sas_url}")
    
  job_sas_list = []
  
  # if the job list is > batch size, remove a batch from the end of the array and submit it for encoding.
  # if the next marker is empty also finish out the job batch in this container
  
  if len(job_input_queue) >= batch_job_size:
    # Submit a batch from the job input queue
    if len(job_input_queue) - batch_job_size > 0:
      job_sas_list = job_input_queue[len(job_input_queue) - batch_job_size:len(job_input_queue)]
      # job_sas_list = job_input_queue[len(job_input_queue) - batch_job_size:len(job_input_queue)]
    else:
      job_sas_list = job_input_queue[0:batch_job_size]
      
  print(f"THERE ARE {len(job_sas_list)} JOBS. JOB SAS LIST: [{job_sas_list}]")
  job_sas_input_list=[]
  skip_extenions = (".ism", ".ismc", ".mpi", ".json")
  for job_sas_input in job_sas_list:
    if job_sas_input.endswith(skip_extenions):
      continue
    else:
      job_sas_input_list.append(job_sas_input)
  print(f"THERE ARE {len(job_sas_input_list)} JOBS. JOB SAS LIST: [{job_sas_input_list}]")
      
  
job_name = 'MyEncodingBatchRemoteH264ContentAwareJob'+ uniqueness
print(f"Creating custom encoding job {job_name}")
  
for sas_url2 in job_sas_input_list:
  # Create Job Input Http and Job Output Asset
  input = JobInputHttp(files=[sas_url2])
  
  print(f"Job Input is: [{vars(input)}]")
  
  out_asset_name = 'outputassetName' + uniqueness
  # create an output Asset
  print(f"Creating output asset {out_asset_name}")
  output_asset = client.assets.create_or_update(resource_group, account_name, out_asset_name, {})
  outputs = JobOutputAsset(asset_name=out_asset_name)
  
  # Create Job object and then create Transform Job
  the_job = Job(input=input, outputs=[outputs])
  job: Job = client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)
  
  job_queue.append(job)
  
  print(f"The Job Queue is: [{(job_queue)}]")
  
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
    job_current = client.jobs.get(resource_group,account_name,transform_name,job_name)
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

if OUTPUT_TO_SAS:
  for job in job_queue:
    if job.outputs:
      job_output = job.outputs[0]
      if PRESERVE_HIERARCHY:
        input_asset = job.input
        if input_asset.files is None:
          raise ValueError("InputAsserts files collection is empty.")
        
        input_path = input_asset.files[0]
        source_file_path = input_path.split("/" + container + "/")[1]
        if not PRESERVE_CONTAINER_PATH:
          source_file_path = source_file_path[1:]
        
        source_file_path = source_file_path[:source_file_path.rfind("/")]
        print(f"SourceFilePath={source_file_path}")
      
      # Next we move the contents of the JobOutputAssets to the container SAS location, optional to delete Assets
      # Keep in mind that you need to use Assets for streaming - so your choice what to do here...
      # print(f"Moving the output of job: {job.name} named: {job_output.asset_name} to the output container SAS location. Delete assets is set to : {delete_source_assets}`)
      # To avoid copying certain files, set the noCopyExtensionFilters array to contain the list of file extensions to ignore.
      