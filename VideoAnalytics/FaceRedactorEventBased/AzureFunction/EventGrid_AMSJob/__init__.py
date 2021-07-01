import json
import logging
import os
from datetime import datetime, timedelta
from urllib.parse import quote

import adal
from msrestazure.azure_active_directory import MSIAuthentication, AdalAuthentication
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (
    Asset,
    Job,
    JobInputHttp,
    JobOutputAsset)
import azure.functions as func
from azure.storage.filedatalake import DataLakeServiceClient, FileSasPermissions, generate_file_sas

def main(event: func.EventGridEvent):
    result = json.dumps({
        'id': event.id,
        'data': event.get_json(),
        'topic': event.topic,
        'subject': event.subject,
        'event_type': event.event_type,
    })

    logging.info('Python EventGrid trigger processed an event: %s', result)

    blob_url = event.get_json().get('url')
    blob_name = blob_url.split("/")[-1].split("?")[0]
    origin_container_name = blob_url.split("/")[-2].split("?")[0]
    storage_account_name = blob_url.split("//")[1].split(".")[0]

    ams_account_name = os.getenv('ACCOUNTNAME')
    resource_group_name = os.getenv('RESOURCEGROUP')
    subscription_id = os.getenv('SUBSCRIPTIONID')
    client_id = os.getenv('AADCLIENTID')
    client_secret = os.getenv('AADSECRET')
    TENANT_ID = os.getenv('AADTENANTID')
    storage_blob_url = 'https://' + storage_account_name + '.blob.core.windows.net/'
    transform_name = 'faceredact'
    LOGIN_ENDPOINT = AZURE_PUBLIC_CLOUD.endpoints.active_directory
    RESOURCE = AZURE_PUBLIC_CLOUD.endpoints.active_directory_resource_id
    
    out_asset_name = 'faceblurringOutput_' + datetime.utcnow().strftime("%m-%d-%Y_%H:%M:%S")
    out_alternate_id = 'faceblurringOutput_' + datetime.utcnow().strftime("%m-%d-%Y_%H:%M:%S")
    out_description = 'Redacted video with blurred faces'

    context = adal.AuthenticationContext(LOGIN_ENDPOINT + "/" + TENANT_ID)
    credentials = AdalAuthentication(context.acquire_token_with_client_credentials, RESOURCE, client_id, client_secret)
    client = AzureMediaServices(credentials, subscription_id)

    output_asset = Asset(alternate_id=out_alternate_id,
                         description=out_description)
    client.assets.create_or_update(
        resource_group_name, ams_account_name, out_asset_name, output_asset)

    token_credential = DefaultAzureCredential()
    datalake_service_client = DataLakeServiceClient(account_url=storage_blob_url,
                                                    credential=token_credential)

    delegation_key = datalake_service_client.get_user_delegation_key(
        key_start_time=datetime.utcnow(), key_expiry_time=datetime.utcnow() + timedelta(hours=1))

    sas_token = generate_file_sas(account_name=storage_account_name, file_system_name=origin_container_name, directory_name="",
                                  file_name=blob_name, credential=delegation_key, permission=FileSasPermissions(read=True),
                                  expiry=datetime.utcnow() + timedelta(hours=1), protocol="https")

    sas_url = "{}?{}".format(quote(blob_url, safe='/:'), sas_token)
    
    job_name = 'Faceblurring-job_' + datetime.utcnow().strftime("%m-%d-%Y_%H:%M:%S")
    job_input = JobInputHttp(label="Video_asset", files=[sas_url])
    job_output = JobOutputAsset(asset_name=out_asset_name)
    job_parameters = Job(input=job_input, outputs=[job_output])

    client.jobs.create(resource_group_name, ams_account_name,
                       transform_name, job_name, parameters=job_parameters)
