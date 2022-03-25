#<TransformImports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.storage.blob import BlobServiceClient
from azure.mgmt.media.models import (
  Transform,
  TransformOutput,
  BuiltInStandardEncoderPreset,
  )

import os
#</TransformImports>

#<ClientEnvironmentVariables>
#Get environment variables
load_dotenv()

# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
default_credential = DefaultAzureCredential()

# The AMS Clients
print("Creating AMS Client")
client = AzureMediaServices(default_credential, os.getenv("SUBSCRIPTIONID"))
#</ClientEnvironmentVariables>

#<CreateTransform>
transform_name='MyTransform'
# From SDK
# TransformOutput(*, preset, on_error=None, relative_priority=None, **kwargs) -> None
# For this snippet, we are using 'AdaptiveStreaming'
transform_output = TransformOutput(preset=BuiltInStandardEncoderPreset(preset_name="AdaptiveStreaming"))
myTransform = Transform()
myTransform.outputs = [transform_output]

# From SDK
# create_or_update(resource_group_name: str, account_name: str, transform_name: str, parameters: "_models.Transform", **kwargs: Any) -> _models.Transform
print("Creating transform " + transform_name)
def createTransform(resource_group_name, account_name, transform_name, parameters):
  transform = client.transforms.create_or_update(os.getenv("RESOURCEGROUP"), os.getenv("ACCOUNTNAME"), transform_name, myTransform)

createTransform(os.getenv("RESOURCEGROUP"), os.getenv("ACCOUNTNAME"), transform_name, myTransform)
#</CreateTransform>

#<DeleteTransform>
# From SDK
# delete(resource_group_name: str, account_name: str, transform_name: str, **kwargs: Any) -> None
def deleteTransform(resource_group_name, account_name, transform_name):
  client.transforms.delete(resource_group_name, account_name, transform_name);
  
deleteTransform(os.getenv("RESOURCEGROUP"), os.getenv("ACCOUNTNAME"), "MyTransform");
#</DeleteTransform>

#<GetTransform>
# From SDK
# get(resource_group_name: str, account_name: str, transform_name: str, **kwargs: Any) -> _models.Transform
def getTransform(resource_group_name, account_name, transform_name):
  results = client.transforms.get(resource_group_name, account_name, transform_name)
  # Results is printed in a JSON format. However, any required information can be returned such as print(results.name)
  print(results)

getTransform(os.getenv("RESOURCEGROUP"), os.getenv("ACCOUNTNAME"), "MyTrans5806")
#</GetTransform>

#<ListTransforms>
# From SDK
# list(resource_group_name: str, account_name: str, filter: Optional[str] = None, orderby: Optional[str] = None, **kwargs: Any) -> Iterable['_models.TransformCollection']
def listTransform(resource_group_name, account_name):
  results = client.transforms.list(resource_group_name, account_name)
  # Iterate over results, which is a collection of Transforms
  for result in results:
    print(result.name)
  
listTransform(os.getenv("RESOURCEGROUP"), os.getenv("ACCOUNTNAME"))
#</ListTransforms>

#<UpdateTransform>
# From SDK
# update(resource_group_name: str, account_name: str, transform_name: str, parameters: "_models.Transform", **kwargs: Any) -> _models.Transform
params = {
  "description": "updated"
}
def updateTransform(resource_group_name, account_name, transform_name, parameters):
  client.transforms.update(resource_group_name, account_name, transform_name, parameters)
  
updateTransform(os.getenv("RESOURCEGROUP"), os.getenv("ACCOUNTNAME"), "MyTrans4272" , params )
#</UpdateTransform>
