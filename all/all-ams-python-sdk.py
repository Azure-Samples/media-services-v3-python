### DO NOT EDIT OR DELETE ###
# This file is for Media Services documentation purposes.

#<EnvironmentVariables>
#Get environment variables
from dotenv import load_dotenv

load_dotenv()

import os

resourceGroup = os.getenv("RESOURCEGROUP")
accountName = os.getenv("ACCOUNTNAME")
subscriptionId = os.getenv('SUBSCRIPTIONID')
#</EnvironmentVariables>

#<DefaultAzureCredential>
# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
from azure.identity import DefaultAzureCredential

defaultCredential = DefaultAzureCredential()
#<DefaultAzureCredential>

# <CreateClient>
# Create an AMS Client
# From SDK
# AzureMediaServices(credentials, subscription_id, base_url=None)
client = AzureMediaServices(defaultCredential, subscriptionId)
# </CreateClient>

# <CreateAsset>
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import Asset

# Set the attributes of the Asset.
assetName = 'myInputasset'
assetAlternateId = 'myInputALTid'
assetDescription = 'myInputDescription'

# Create an Asset object
# From the SDK
# Asset(*, alternate_id: str = None, description: str = None, container: str = None, storage_account_name: str = None, **kwargs) -> None
assetObj = Asset(alternate_id=assetAlternateId,description=assetDescription)

# Create am Asset
# From SDK
# create_or_update(resource_group_name, account_name, asset_name, parameters, custom_headers=None, raw=False, **operation_config)
asset = client.assets.create_or_update(resourceGroup, accountName, assetName, assetObj)
# </CreateAsset>

#<CreateTransform>
from azure.mgmt.media import AzureMediaServices
# You can use a StandardEncoderPreset instead of a BuiltInStandardEncoder preset
from azure.mgmt.media.models import (Transform, TransformOutput, BuiltInStandardEncoderPreset)

### Create a Transform ###
transformName='myTransform'
# From SDK
# TransformOutput(*, preset, on_error=None, relative_priority=None, **kwargs) -> None
# This example uses the BuiltInStandardEncoder preset called AdaptiveStreaming
transformOutputObj = TransformOutput(preset=BuiltInStandardEncoderPreset(preset_name="AdaptiveStreaming"))

#Create a transform object
transformObj = Transform()

#Create the transform outputs
transformObj.outputs = [transformOutputObj]

# From SDK
# Create_or_update(resource_group_name, account_name, transform_name, outputs, description=None, custom_headers=None, raw=False, **operation_config)
transform = client.transforms.create_or_update(
  resource_group_name=resourceGroup,
  account_name=accountName,
  transform_name=transformName,
  parameters = transformObj)
#</CreateTransform>

#</CreateJob>
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (Job, JobInputAsset, JobOutputAsset)

# The file you want to upload.  For this example, put the file in the same folder as this script. 
# The file ignite.mp4 has been provided for you. 
source_file = "ignite.mp4"

### Create a Job ###
# To create a job you need an input asset and an output asset.
job_name = 'MyJob'
files = (source_file)

# From SDK
# JobInputAsset(*, asset_name: str, label: str = None, files=None, **kwargs) -> None
input = JobInputAsset(asset_name=inputAssetName)

# From SDK
# JobOutputAsset(*, asset_name: str, **kwargs) -> None
outputObj = JobOutputAsset(asset_name=outputAssetName)

# From SDK
# Job(*, input, outputs, description: str = None, priority=None, correlation_data=None, **kwargs) -> None
theJob = Job(input=input,outputs=[output])
# From SDK
# Create(resource_group_name, account_name, transform_name, job_name, parameters, custom_headers=None, raw=False, **operation_config)
job: Job = client.jobs.create(resourceGroup),accountName,transform_name,job_name,parameters=theJob)
#</CreateJob>