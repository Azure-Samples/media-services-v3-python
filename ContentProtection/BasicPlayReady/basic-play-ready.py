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
  ContentKeyPolicy,
  ContentKeyPolicySymmetricTokenKey,
  ContentKeyPolicyTokenClaim,
  ContentKeyPolicyOption,
  ContentKeyPolicyTokenRestriction,
  ContentKeyPolicyRestrictionTokenType,
  ContentKeyPolicyPlayReadyConfiguration,
  ContentKeyPolicyPlayReadyLicense,
  ContentKeyPolicyPlayReadyContentEncryptionKeyFromHeader,
  ContentKeyPolicyPlayReadyPlayRight,
  ContentKeyPolicyPlayReadyExplicitAnalogTelevisionRestriction,
  ContentKeyPolicyPlayReadyLicenseType,
  ContentKeyPolicyPlayReadyContentType,
  StreamingLocator
)
import jwt
import os
import base64

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

# The file you want to upload.  For this example, put the file in the same folder as this script. 
# The file ignite.mp4 has been provided for you. 
source_file = "ignite.mp4"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "DRM-PlayReady-" + str(random.randint(0,9999))
content_key_policy_name = 'CommonEncryptionCencDrmContentKeyPolicy_2022_05_25_PlayReady'
symmetric_key = os.getenv('DRMSYMMETRICKEY')

# DRM Configuration Settings
issuer = 'my_issuer'
audience = 'my_audience'

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

transform_name = 'ContentAwareEncodingTransform'

# Create a new Standard encoding Transform for Built-in Copy Codec
print(f"Creating Encoding transform named: {transform_name}")
# For this snippet, we are using 'BuiltInStandardEncoderPreset'
transform_output = TransformOutput(
  preset = BuiltInStandardEncoderPreset(
    preset_name = "ContentAwareEncoding"
  ),
  # What should we do with the job if there is an error?
  on_error=OnErrorType.STOP_PROCESSING_JOB,
  # What is the relative priority of this job to others? Normal, high or low?
  relative_priority=Priority.NORMAL
)

print("Creating encoding transform...")

# Adding transform details
myTransform = Transform()
myTransform.description="Transform with Basic Play Ready"
myTransform.outputs = [transform_output]

print(f"Creating transform {transform_name}")
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=transform_name,
  parameters=myTransform)

print(f"{transform_name} created (or updated if it existed already). ")

job_name = 'StreamBasic'+ uniqueness
print(f"Creating custom encoding job {job_name}")
files = (source_file)

# Create Job Input and Job Output Assets
input = JobInputAsset(asset_name=in_asset_name)
outputs = JobOutputAsset(asset_name=out_asset_name)

# Create a Job object and then create a transform job
theJob = Job(input=input,outputs=[outputs])
job: Job = client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=theJob)

# Set a token signing key that you want to use from the .env file
# WARNING: This is an important secret when moving to a production system and should be kept in a Key Vault.
token_signing_key = base64.b64decode(symmetric_key)

# Create the content key policy that configures how the content key is delivered to end clients
# via the Key Delivery component of Azure Media Services.
# We are using the ContentKeyIndentifierClaim in the ContentKeyPolicy which means that the token presented
# to the Key Delivery Component must have the identifier of the content key in it.

primary_key = ContentKeyPolicySymmetricTokenKey(
  key_value=token_signing_key
)

restriction = ContentKeyPolicyTokenRestriction(
  issuer=issuer,
  audience=audience,
  primary_verification_key=primary_key,
  restriction_token_type=ContentKeyPolicyRestrictionTokenType.JWT,
  alternate_verification_keys=None,
  required_claims=None
)

# Creates a PlayReady License Template with the following settings
# - sl2000
# - license type = non-persistent
# - content type = unspecified
# - Uncompressed Digital Video OPL = 270
# - Compressed Digital Video OPL  = 300
# - Explicit Analog Television Protection =  best effort
play_ready_config = ContentKeyPolicyPlayReadyConfiguration(
  licenses=[
    ContentKeyPolicyPlayReadyLicense(
      allow_test_devices=True,
      content_key_location=ContentKeyPolicyPlayReadyContentEncryptionKeyFromHeader(),
      play_right=ContentKeyPolicyPlayReadyPlayRight(
        allow_passing_video_content_to_unknown_output="Allowed",
        image_constraint_for_analog_component_video_restriction=True,
        digital_video_only_content_restriction=False,
        uncompressed_digital_video_opl=270,
        compressed_digital_video_opl=400,
        image_constraint_for_analog_computer_monitor_restriction=False,
        explicit_analog_television_output_restriction=ContentKeyPolicyPlayReadyExplicitAnalogTelevisionRestriction(
          best_effort=True,
          configuration_data=2
        )
      ),
      license_type=ContentKeyPolicyPlayReadyLicenseType.NON_PERSISTENT,
      content_type=ContentKeyPolicyPlayReadyContentType.UNSPECIFIED
    )
  ]
)

# Add the license type configurations for PlayReady to the policy
options = [
  ContentKeyPolicyOption(
    configuration=play_ready_config,
    restriction=restriction
  )
]

create_content_policy = client.content_key_policies.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  content_key_policy_name=content_key_policy_name,
  parameters=ContentKeyPolicy(
    description="Content Key Policy Playready",
    options=options
  )
)

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
locator_name = f"locator-{uniqueness}"
if output_asset:
  streaming_locator = StreamingLocator(asset_name=out_asset_name, streaming_policy_name="Predefined_MultiDrmCencStreaming", default_content_key_policy_name=content_key_policy_name)
  locator = client.streaming_locators.create(
    resource_group_name=resource_group,
    account_name=account_name,
    streaming_locator_name=locator_name,
    parameters=streaming_locator
  )
  
  key_identifier=''
  
  # Since we didn't specify a content key when creating the StreamingLocator, the service created a random GUID for us.
  if locator.content_keys:
    key_identifier = locator.content_keys[0].id
    print(f"The ContentKey for this streaming locator is: {key_identifier}")
  else:
    raise ValueError("Locator and content keys are undefined.")
  
  start_date = int(time.time()) - (5*60)      # Get the current time and subtract 5 minutes, then return as a Unix timestamp
  end_date = int(time.time()) + (24*60*60)    # Expire the token in 1 day, return Unix timestamp

  jwt_token = jwt.encode(
    payload={
      "exp": end_date,
      "nbf": start_date,
      "iss": issuer,
      "aud": audience
    },
    key=token_signing_key,
    algorithm="HS256",
  )
  
  print(f"The JWT token used is: {jwt_token}")
  print("You can decode the token using a tool like https://www.jsonwebtoken.io/ with the symmetric encryption key to view the decoded results.")
  
  streaming_endpoint_name = "default"
  
  if locator:
    # Get the default streaming endpoint on the account
    streaming_endpoint = client.streaming_endpoints.get(
      resource_group_name=resource_group,
      account_name=account_name,
      streaming_endpoint_name=streaming_endpoint_name
    )
    
    if streaming_endpoint.resource_state != "Running":
      print(f"Streaming endpoint is stopped. Starting the endpoint named {streaming_endpoint_name}...")
      client.streaming_endpoints.begin_start(resource_group, account_name, streaming_endpoint_name)
      print("Streaming Endpoint started.")
      
    paths = client.streaming_locators.list_paths(
      resource_group_name=resource_group,
      account_name=account_name,
      streaming_locator_name=locator_name 
    )
    if paths.streaming_paths:
      print("The streaming links: ")
      for path in paths.streaming_paths:
        for format_path in path.paths:
          manifest_path = "https://" + streaming_endpoint.host_name + format_path
          print(manifest_path)
          print("IMPORTANT!! For all DRM Samples to work, you must use an HTTPS hosted player page.")
          print("For PlayReady testing, please open the link in the Microsoft Edge Browser.")
          print(f"Click to playback in AMP player: https://ampdemo.azureedge.net/?url={manifest_path}&playready=true&token=Bearer%20{jwt_token}")
      print("The output asset for streaming via HLS or DASH was successful!")
    else:
      raise Exception("Locator was not created or {locator.name} is undefined.")
