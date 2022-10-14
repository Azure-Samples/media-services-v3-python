# These code snippets are used in Azure Media Services documentation.
# DO NOT EDIT

#<ContentKeyPoliciesImports>
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (
    ContentKeyPolicy, 
    ContentKeyPolicyOption, 
    ContentKeyPolicyPlayReadyConfiguration, 
    ContentKeyPolicyPlayReadyLicense, 
    ContentKeyPolicyPlayReadyLicenseType,
    ContentKeyPolicyPlayReadyContentEncryptionKeyFromHeader,
    ContentKeyPolicyPlayReadyContentType,
    ContentKeyPolicyOpenRestriction
)
import os
#</ContentKeyPoliciesImports>

#<EnvironmentVariables>
# Get environment variables
load_dotenv()

subscription_id = os.getenv("SUBSCRIPTIONID")
account_name=os.getenv("ACCOUNTNAME")
resource_group_name=os.getenv("RESOURCEGROUP")
client_id = os.getenv("AZURE_CLIENT_ID")
storage_account_name=os.getenv("STORAGEACCOUNTNAME")
#</EnvironmentVariables>

#<CreateAMSClient>
# Create the Media Services client and authenticate using the DefaultAzureCredential
default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)
client = AzureMediaServices(default_credential, subscription_id)
#</CreateAMSClient>

#<CreateContentKeyPolicy>
# Set the name of the Content Key Policy you want to create
content_key_policy_name = "mytestcontentkeypolicy"

# Set the Content Key Policy description and Options
# For this sample, we are using PlayReadyConfiguration that requires PlayReadyLicense
# For the PlayReadyLicense, the type is PERSISTENT and content type is set to ULTRA_VIOLET_DOWNLOAD
# If you wish to change these settings, please visit: https://docs.microsoft.com/en-us/python/api/azure-mgmt-media/azure.mgmt.media.models.contentkeypolicyplayreadylicense?view=azure-python
# for documentation.
# Also, this sample uses Open Restriction.
content_key_policy_description = "mytestcontentkeypolicydescription"
content_key_policy_license = [ContentKeyPolicyPlayReadyLicense(
    allow_test_devices=True,
    license_type=ContentKeyPolicyPlayReadyLicenseType.PERSISTENT,
    content_key_location=ContentKeyPolicyPlayReadyContentEncryptionKeyFromHeader(),
    content_type=ContentKeyPolicyPlayReadyContentType.ULTRA_VIOLET_DOWNLOAD
)]
content_key_policy_configuration = ContentKeyPolicyPlayReadyConfiguration(licenses=content_key_policy_license)
content_key_policy_restriction = ContentKeyPolicyOpenRestriction()
content_key_policy_option = [ContentKeyPolicyOption(configuration=content_key_policy_configuration, restriction=content_key_policy_restriction)]
content_key_policy = ContentKeyPolicy(description=content_key_policy_description, options=content_key_policy_option)

# From SDK
# create_or_update(resource_group_name: str, account_name: str, content_key_policy_name: str, parameters: "_models_py3.ContentKeyPolicy", **kwargs: Any) -> _models_py3.ContentKeyPolicy
def create_content_key_policy(resource_group_name, account_name, content_key_policy_name, parameters):
    content_key_policy = client.content_key_policies.create_or_update(resource_group_name, account_name, content_key_policy_name, parameters)
    
create_content_key_policy(resource_group_name, account_name, content_key_policy_name, content_key_policy)
#</CreateContentKeyPolicy>

#<GetContentKeyPolicy>
# From SDK
# get(resource_group_name: str, account_name: str, content_key_policy_name: str, **kwargs: Any) -> _models_py3.ContentKeyPolicy
def get_content_key_policy(resource_group_name, account_name, content_key_policy_name):
    results = client.content_key_policies.get(resource_group_name, account_name, content_key_policy_name)
    # You can get any properties of a content key policy. Here, we are printing the content key policy name.
    print(results.description)
    
get_content_key_policy(resource_group_name, account_name, content_key_policy_name)
#</GetContentKeyPolicy>

#<GetContentKeyPolicyPropertiesWithSecrets>
# From SDK
# get_policy_properties_with_secrets(resource_group_name: str, account_name: str, content_key_policy_name: str, **kwargs: Any) -> _models_py3.ContentKeyPolicyProperties
def get_content_key_policy_with_secrets(resource_group_name, account_name, content_key_policy_name):
    results = client.content_key_policies.get_policy_properties_with_secrets(resource_group_name, account_name, content_key_policy_name)
    # You can get any properties of Content Key Policy secret. Here we are printing the entire Content Key Policy with secrets.
    print(results)
    
get_content_key_policy_with_secrets(resource_group_name, account_name, content_key_policy_name)
#</GetContentKeyPolicyPropertiesWithSecrets>

#<ListContentKeyPolicy>
# From SDK:
# list(resource_group_name: str, account_name: str, filter: Optional[str] = None, top: Optional[int] = None, orderby: Optional[str] = None, **kwargs: Any) -> Iterable[_models_py3.ContentKeyPolicyCollection]
def list_content_key_policy(resource_group_name, account_name):
    results = client.content_key_policies.list(resource_group_name, account_name)
    # You can add additional functions such as filter, orderby etc. Here, we are printing the entire Content Key Policies in the current Media Services Account
    for i in results:
        print(i.name)
    
list_content_key_policy(resource_group_name, account_name)
#</ListContentKeyPolicy>

#<UpdateContentKeyPolicy>
content_key_policy_object = ContentKeyPolicy(description="myupdatedtestcontentkeypolicydescription")

# From SDK
# update(resource_group_name: str, account_name: str, content_key_policy_name: str, parameters: _models_py3.ContentKeyPolicy, **kwargs: Any) -> _models_py3.ContentKeyPolicy
def update_content_key_policy(resource_group_name, account_name, content_key_policy_name, parameters):
    client.content_key_policies.update(resource_group_name, account_name, content_key_policy_name, parameters)
    
update_content_key_policy(resource_group_name, account_name, content_key_policy_name, content_key_policy_object)
#</UpdateContentKeyPolicy>

#<DeleteContentKeyPolicy>
# From SDK
# delete(resource_group_name: str, account_name: str, content_key_policy_name: str, **kwargs: Any) -> None
def delete_content_key_policy(resource_group_name, account_name, content_key_policy_name):
    client.content_key_policies.delete(resource_group_name, account_name, content_key_policy_name)
    
delete_content_key_policy(resource_group_name, account_name, content_key_policy_name)
#</DeleteContentKeyPolicy>
