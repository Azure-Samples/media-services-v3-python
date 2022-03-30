#author: IngridAtMicrosoft

#<TransformsImports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
# BuiltInEncoderPreset is used here but you should import the preset that you want to use.
from azure.mgmt.media.models import (Transform,TransformOutput,BuiltInStandardEncoderPreset)
import os
#</TransformsImports>

#<EnvironmentVariables>
# Get environment variables
load_dotenv()

subscriptionId = os.getenv("SUBSCRIPTIONID")
accountName=os.getenv("ACCOUNTNAME")
resourceGroupName=os.getenv("RESOURCEGROUP")
clientId = os.getenv("AZURE_CLIENT_ID")
storageAccountName=os.getenv("STORAGEACCOUNTNAME")
#</EnvironmentVariables>

#<CreateAMSClient>
# Create the Media Services client and authenticate using the DefaultAzureCredential
default_credential = DefaultAzureCredential()
# From SDK
# AzureMediaServices(credentials, subscription_id, base_url=None)
client = AzureMediaServices(default_credential, subscriptionId)
#</CreateAMSClient>

#<TransformCreate>
# Create a Transform
# Set the name of the transform you want to create.
transformName='MyTransform'

# Create at least one transform output.
# Don't forget to import the preset that you want to use.
# From SDK
# TransformOutput(*, preset, on_error=None, relative_priority=None, **kwargs) -> None
transform_output = TransformOutput(preset=BuiltInStandardEncoderPreset(preset_name="AdaptiveStreaming"))

# Add the transform output to the outputs list
outputs = [transform_output]

# Create the transform object
# From SDK
# Transform(*, description: Optional[str] = None, outputs: Optional[List[azure.mgmt.media.models._models_py3.TransformOutput]] = None, **kwargs)
transform = Transform(description="My description",outputs=outputs)

print("Creating transform " + transformName)
# From SDK
# Create_or_update(resource_group_name, account_name, transform_name, outputs, description=None, custom_headers=None, raw=False, **operation_config)

def createTransform(resource_group_name, account_name, transform_name,transform):
    client.transforms.create_or_update(resource_group_name,account_name,transform_name,transform)

createTransform(resourceGroupName,accountName,transformName,transform)
#</TransformCreate>

#<TransformList>
# List the transforms in a Media Services account
# From SDK
# list(resource_group_name: str, account_name: str, filter: Optional[str] = None, orderby: Optional[str] = None, **kwargs: Any) -> Iterable['_models.TransformCollection']

def listTransforms(resource_group_name, account_name):
    # Results will contain a list of transforms.
    results = client.transforms.list(resource_group_name, account_name)
    # Iterate through the transform list and return the name of each transform
    for result in results:
        print(result.name)
listTransforms(resourceGroupName,accountName)
#</TransformList>

#<TransformGet>
# Set the name of the transform for which you want properties.
transformName='MyTransform'

# From SDK
# get(resource_group_name: str, account_name: str, transform_name: str, **kwargs: Any) -> _models.Transform
def getTransform(resource_group_name, account_name, transform_name):
    results=client.transforms.get(resource_group_name, account_name, transform_name)
    #You can get any of the properties of a transform.  Here we are printing the transform name and description
    print(results.name)
    print(results.description)

getTransform(resourceGroupName,accountName,transformName)
#</TransformGet>

#<TransformUpdate>
# Set the name of the transform that you want to update.
transformName='MyTransform'

# Change the description of an existing transform by creating a transform object for the update function.
transform1 = Transform(description="My new description")

# From SDK
# update(resource_group_name: str, account_name: str, transform_name: str, parameters: "_models.Transform", **kwargs: Any) -> _models.Transform
def updateTransform(resource_group_name, account_name, transform_name,transform):
    client.transforms.update(resource_group_name, account_name, transform_name,transform)
updateTransform(resourceGroupName,accountName,transformName,transform1)
#</TransformUpdate>

#<TransformDelete>
# Set the name of the transform you want to delete.
transformName='MyTransform'

# From SDK
# delete(resource_group_name: str, account_name: str, transform_name: str, **kwargs: Any) -> None
def deleteTransform(resource_group_name, account_name, transform_name):
    client.transforms.delete(resource_group_name, account_name, transform_name)

deleteTransform(resourceGroupName,accountName,transformName)
#</TransformDelete>
