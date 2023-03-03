from datetime import date, datetime, timedelta, timezone
import asyncio
import os
from urllib.parse import urlparse
from warnings import catch_warnings
from azure.mgmt.media.aio import AzureMediaServices
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import (BlobServiceClient, BlobClient)
from azure.mgmt.media.models import (
    StreamingLocator,
    Job,
    JobInputs,
    JobInputAsset,
    JobOutputAsset,
    JobInputHttp,
    ListContainerSasInput,
    AudioTrack
)
from azure.core.exceptions import (ResourceNotFoundError)

# Get the environment variables SUBSCRIPTION_ID, RESOURCE_GROUP and ACCOUNT_NAME

#client = "not set"
account_name = "global variable not set"
resource_group = "global variable not set"
remote_sas_url = "global variable not set"
subscription_id = "global variable not set"
blob_service_client = BlobServiceClient
default_credential = DefaultAzureCredential
client = AzureMediaServices



def set_account_name(account):
    #print("setAccountName called")
    global account_name
    #print("Before: " + account_name)
    account_name = account
    #print("After: " + account_name)
def set_resource_group(group_name):
    #print("setResourceGroupe called")
    global resource_group
    #print("Before: " + resource_group)
    resource_group = group_name
    #print("After: " + resource_group)
# No need for this function
def set_remote_storage_sas(remote_sasurl):
    #print("setRemoteStorageSas called")
    global remote_sas_url
    #print("Before: " + remote_sas_url)
    remote_sas_url = remote_sasurl
    #print("After: " + remote_sas_url)
def set_subscription_id(sub_id):
    #print("setSubscriptionId called")
    global subscription_id
    #print("Before: " + subscription_id)
    subscription_id = sub_id
    #print("After: " + subscription_id)

# Create the default credential
def create_default_azure_credential(defaultCredential):
    global default_credential
    default_credential = defaultCredential

# # Create clients
# def create_blob_service_client(blobSClient):
#    global blob_service_client
#    blob_service_client = blobSClient

def create_azure_media_services(ams_account):
    global client
    client = ams_account

# Since the media folder would have a different relative path, his sets the location of the media files
# so that it is relative to the helper function script. All that is passed to the helper function is the file name.

media_folder = "C:\\Users\\inhenkel\\Documents\\AMSPython\\media-services-v3-python-03-02-2023\\Media\\"
#media_folder = "../../Media/"

async def submit_job(transform_name, job_name, job_input, output_asset_name, preset_override = None):
    if output_asset_name is None:
        raise ValueError("OutputAsset Name is not defined. Check creation of the output asset")

    job_outputs = [JobOutputAsset(asset_name=output_asset_name, preset_override=preset_override)]
    the_job = Job(input=job_input, outputs=job_outputs)

    return await client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)


async def submit_job_multi_outputs(transform_name, job_name, job_input, job_outputs):
    the_job = Job(input=job_input, outputs=job_outputs)
    return await client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)


async def submit_job_multi_inputs(transform_name, job_name, job_inputs, output_asset_name):
    if output_asset_name is None:
        raise ValueError("OutputAsset Name is not defined. Check creation of the output asset")

    job_inputs = JobInputs(inputs=job_inputs)
    job_outputs = [JobOutputAsset(asset_name=output_asset_name)]
    the_job = Job(input=job_inputs, outputs=job_outputs)

    return await client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)


async def submit_job_with_input_sequence(transform_name, job_name, input_sequence, output_asset_name):
    if output_asset_name is None:
        raise ValueError("OutputAsset Name is not defined. Check creation of the output asset")

    job_outputs = [JobOutputAsset(asset_name=output_asset_name)]
    the_job = Job(input=input_sequence, outputs=job_outputs)

    return await client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)


async def submit_job_with_track_definitions(transform_name, job_name, job_input, output_asset_name, input_definitions):
    if output_asset_name is None:
        raise ValueError("OutputAsset Name is not defined. Check creation of the output asset")

    job_input_with_track_definitions = job_input
    job_input_with_track_definitions.input_definitions = input_definitions

    job_outputs = [JobOutputAsset(asset_name=output_asset_name)]
    the_job = Job(input=job_input_with_track_definitions, outputs=job_outputs)

    return await client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)

async def update_tracks(asset_name,track_name, parameters):
    try:
        await client.tracks.begin_create_or_update(resource_group_name=resource_group,account_name=account_name,asset_name=asset_name,track_name=track_name,parameters=parameters)
    except Exception as e:
        print(e)

async def upload_file(asset_name,input_file):
# Set permissions for SAS URL and expiry time (for the sample, we used expiry time to be 1 additional hours from current time)
    print("Setting permissions for SAS URL and expiry time.")
    # Make sure that the expiry time is far enough in the future that you can keep using it until you are done testing.
    input = ListContainerSasInput(permissions="ReadWrite", expiry_time=datetime.now(timezone.utc)+timedelta(hours=24))
    print("Listing the container sas.")
    list_container_sas = await client.assets.list_container_sas(resource_group, account_name, asset_name, parameters=input)
    if list_container_sas.asset_container_sas_urls:
        upload_sas_url = list_container_sas.asset_container_sas_urls[0]
        file_name = os.path.basename(input_file)
        sas_uri = urlparse(upload_sas_url)

        # Get the Blob service client using the Asset's SAS URL
        blob_service_client = BlobServiceClient(upload_sas_url)
        # We need to get the container_name here from the SAS URL path to use later when creating the container client
        # Change the path to the container so that it doesn't make "subdirectories"
        no_slash = sas_uri.path.replace("/","../")
        container_name = no_slash
        # print(f"Container name: ", container_name)
        container_client = blob_service_client.get_container_client(container_name)
        # Next, get the block_blob_client needed to use the uploadFile method
        blob_client = container_client.get_blob_client(file_name)
        # print(f"Block blob client: ", blob_client)

        print(f"Uploading file named {file_name} to blob in the Asset's container...")
        print("Uploading blob...")
        file_path = media_folder + file_name
        print("Video is located in " + file_path)
        with open(file_path, "rb") as data:
            await blob_client.upload_blob(data, max_concurrency=5)
        print(f"File {file_name} successfully uploaded!")

    print("Closing Blob service client")
    print()
    await blob_service_client.close()



# Creates a new Media Services Asset, which is a pointer to a storage container
# Uses the Storage Blob npm package to upload a local file into the container through the use
# of the SAS URL obtained from the new Asset object.
# This demonstrates how to upload local files up to the container without requiring additional storage credential.
async def create_input_asset(asset_name, input_file):
    print(f"create_input_asset called for asset_name: ", asset_name, "Input file: ", input_file)
    upload_sas_url = ""
    file_name = ""
    sas_uri=""
    print ("Creating asset for: ", "resource_group: ", resource_group, "account_name: ", account_name, "asset_name: ", asset_name)
    asset = await client.assets.create_or_update(resource_group, account_name, asset_name, {})
    if asset:
        print("Asset created.")
    else:
        print("There was a problem creating an asset.")

    await upload_file(asset_name=asset_name,input_file=input_file)

    """
    # Set permissions for SAS URL and expiry time (for the sample, we used expiry time to be 1 additional hours from current time)
    print("Setting permissions for SAS URL and expiry time.")
    # Make sure that the expiry time is far enough in the future that you can keep using it until you are done testing.
    input = ListContainerSasInput(permissions="ReadWrite", expiry_time=datetime.now(timezone.utc)+timedelta(hours=24))
    print("Listing the container sas.")
    list_container_sas = await client.assets.list_container_sas(resource_group, account_name, asset_name, parameters=input)
    if list_container_sas.asset_container_sas_urls:
        upload_sas_url = list_container_sas.asset_container_sas_urls[0]
        file_name = os.path.basename(input_file)
        sas_uri = urlparse(upload_sas_url)

        # Get the Blob service client using the Asset's SAS URL
        blob_service_client = BlobServiceClient(upload_sas_url)
        # We need to get the container_name here from the SAS URL path to use later when creating the container client
        # Change the path to the container so that it doesn't make "subdirectories"
        no_slash = sas_uri.path.replace("/","../")
        container_name = no_slash
        # print(f"Container name: ", container_name)
        container_client = blob_service_client.get_container_client(container_name)
        # Next, get the block_blob_client needed to use the uploadFile method
        blob_client = container_client.get_blob_client(file_name)
        # print(f"Block blob client: ", blob_client)

        print(f"Uploading file named {file_name} to blob in the Asset's container...")
        print("Uploading blob...")
        file_path = media_folder + file_name
        print("Video is located in " + file_path)
        with open(file_path, "rb") as data:
            await blob_client.upload_blob(data, max_concurrency=5)
        print(f"File {file_name} successfully uploaded!")

    print("Closing Blob service client")
    print()
    await blob_service_client.close()
    """

    return asset



async def wait_for_job_to_finish(transform_name, job_name):
    timeout = datetime.now(timezone.utc)
    # Timer values
    timeout_seconds = 60 * 10
    sleep_interval = 10

    timeout += timedelta(seconds=timeout_seconds)

    async def poll_for_job_status():
        job = await client.jobs.get(resource_group, account_name, transform_name, job_name)

        # Note that you can report the progress for each Job Output if you have more than one. In this case, we only have one output in the Transform
        # that we defined in this sample, so we can check that with the job.outputs[0].progress parameter.
        if job.outputs != None:
            # print(f"Job.outputs[0] is: {job.outputs[0]}")
            print(f"Job State is: {job.state}, \tProgress: {job.outputs[0].progress}%")
        if job.state == 'Finished' or job.state == 'Error' or job.state == 'Canceled':
            return job
        elif datetime.now(timezone.utc) > timeout:
            return job
        else:
            await asyncio.sleep(sleep_interval)
            return await poll_for_job_status()

    return await poll_for_job_status()


async def wait_for_all_jobs_to_finish(transform_name, job_queue, current_container, batch_counter):
    sleep_interval = 10
    batch_processing = True
    while batch_processing:
        error_count = 0
        finished_count = 0
        processing_count = 0
        output_rows = []

        for job_item in job_queue:
            if job_item is not None:
                job = await client.jobs.get(resource_group, account_name, transform_name, job_item.name)

                if job.outputs is not None:
                    output_rows.append({
                        'Start': "starting" if (job.start_time is None) else job.start_time.strftime("%H:%M:%S"),
                        'Job': job.name,
                        'State': job.state,
                        'Progress': job.outputs[0].progress,
                        'End': "---" if (job.end_time is None) else job.end_time.strftime("%H:%M:%S")
                    })

                if job.state == 'Error' or job.state == 'Canceled':
                    if job.input:
                        update_job_input_metadata(job.input, { "ams_encoded": "false", "ams_status": job.state })
                    error_count+=1
                elif job.state == 'Finished':
                    # Update the source blob metadata to note that we encoded it already, the date it was encoded, and the transform name used
                    if job.input:
                        update_job_input_metadata(job.input,
                                               {
                                                   "ams_encoded": "true",
                                                   "ams_status": job.state,
                                                   "ams_encoded_date": datetime.now(timezone.utc).strftime("%m/%d/%Y"),
                                                   "ams_transform": transform_name
                                               })
                    finished_count+=1

                elif job.state == 'Processing' or job.state == 'Scheduled':
                    processing_count+=1

        print(f"\n----------------------------------------\tENCODING BATCH  #{batch_counter}       ----------------------------------------------------")
        print(f"Current Container: {current_container}")
        print(f"Encoding batch size: {len(job_queue)}\t Processing: {processing_count}\t Finished: {finished_count}\t Error: {error_count}")
        print("-------------------------------------------------------------------------------------------------------------------------------")
        print(output_rows)

        # If the count of finished and error jobs add up to the length of the queue batch, then break out.
        if finished_count + error_count == len(job_queue):
            batch_processing = False

        await asyncio.sleep(sleep_interval)


async def update_job_input_metadata(job_input, metadata):
    if job_input is not None:
        if job_input.files:
            # This sample assumes that the input files URL [0] is a SAS URL
            blob_client = BlobClient(remote_sas_url)

            try:
                await blob_client.set_blob_metadata(metadata)
            except:
                print("Error updating the metadata on the JobInput. Please check to make sure that the source SAS URL allows writes to update metadata.")


async def download_results(asset_name, results_folder):
    input = ListContainerSasInput(permissions="Read", expiry_time=datetime.now(timezone.utc)+timedelta(hours=24))
    list_container_sas = await client.assets.list_container_sas(resource_group, account_name, asset_name, parameters=input)


    if list_container_sas.asset_container_sas_urls:
        container_sas_url = list_container_sas.asset_container_sas_urls[0]
        sas_uri = urlparse(container_sas_url)

        # Get the Blob service client using the Asset's SAS URL
        blob_service_client = BlobServiceClient(container_sas_url)
        # We need to get the containerName here from the SAS URL path to use later when creating the container client
        container_name = sas_uri.path.replace("/", "../")

        """
        print(f"Container_name is: {container_name}")
        print(f"The results folder is: {results_folder}")
        print(f"Asset_name is: {asset_name}")
        """

        directory = os.path.join(results_folder, asset_name) + '/'
        print(f"Downloading output into {directory}")

        # Get the blob container client using the container name on the SAS URL path
        # to access the block_blob_client needed to use the upload_file method
        container_client = blob_service_client.get_container_client(container_name)

        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as err:
            print(err)

        print(f"Listing blobs in container {container_name}")
        print("Downloading blobs to local directory in background...")

        i = 1
        try:
            async for blob in container_client.list_blobs():
                print(f"Blob {i}: {blob.name}")

                blob_client = container_client.get_blob_client(blob.name)
                download_file_path = directory + os.path.basename(blob.name)
                # print(f"The download file path is: {download_file_path}")
                try:
                    with open(download_file_path, 'wb') as file:
                        files = await blob_client.download_blob()
                        file.write(await files.readall())

                    # await block_blob_client.download_blob()
                except ResourceNotFoundError:
                    print("No blob found.")
            print("Downloading results complete! Exiting the program now...")
            print()

        except:
            print("There was an error listing and/or downloading the blobs.")

    print("Closing blob service client")
    await blob_service_client.close()


# Selects the JobInput type to use based on the value of input_file or input_url.
# Set input_file to null to create a job input that sources from an HTTP URL path
# Creates a new input Asset and uploads the local file to it before returning a JobInput object.
# Returns a JobInputHttp object if input_file is set to null, and the input_url is set to a valid URL
async def get_job_input_type(input_file, input_url, name_prefix, uniqueness):
    if input_file is not None:
        asset_name = name_prefix + "-input-" + uniqueness
        await create_input_asset(asset_name, input_file)
        return JobInputAsset(asset_name=asset_name)
    else:
        return JobInputHttp(files=[input_url])


async def create_streaming_locator(asset_name, locator_name):
    streaming_locator = StreamingLocator(asset_name=asset_name, streaming_policy_name="Predefined_ClearStreamingOnly")
    locator = await client.streaming_locators.create(
        resource_group_name = resource_group,
        account_name = account_name,
        streaming_locator_name= locator_name,
        parameters = streaming_locator
    )

    return locator


async def get_streaming_urls(locator_name):
    streaming_endpoint = await client.streaming_endpoints.get(
      resource_group_name = resource_group,
      account_name = account_name,
      streaming_endpoint_name = "default"
    )
    paths = await client.streaming_locators.list_paths(
      resource_group_name = resource_group,
      account_name = account_name,
      streaming_locator_name = locator_name
    )
    if paths.streaming_paths:
      print("The streaming links: ")
      for path in paths.streaming_paths:
        for format_path in path.paths:
          manifest_path = "https://" + streaming_endpoint.host_name + format_path
          print(manifest_path)
          print(f"Click to playback in AMP player: http://ampdemo.azureedge.net/?url={manifest_path}")
      print("The output asset for streaming via HLS or DASH was successful!")
    else:
        raise Exception("Locator was not created or Locator.name is undefined")


# This method builds the manifest URL from the static values used during creation of the Live Output.
# This allows you to have a deterministic manifest path. <streaming endpoint hostname>/<streaming locator ID>/manifestName.ism/manifest(<format string>)
async def build_manifest_paths(streaming_locator_id, manifest_name, filter_name, streaming_endpoint_name):
    hls_format = "format=m3u8-cmaf"
    dash_format = "format=mpd-time-cmaf"

    # Get the default streaming endpoint on the account
    streaming_endpoint = await client.streaming_endpoints.get(
      resource_group_name = resource_group,
      account_name = account_name,
      streaming_endpoint_name = streaming_endpoint_name
    )

    if streaming_endpoint.resource_state != "Running":
      print(f"Streaming endpoint is stopped. Starting endpoint named {streaming_endpoint_name}")
      client.streaming_endpoints.begin_start(resource_group, account_name, streaming_endpoint_name)

    manifest_base = f"https://{streaming_endpoint.host_name}/{streaming_locator_id}/{manifest_name}.ism/mainfest"

    hls_manifest = ""
    if filter_name is None:
      hls_manifest = f'{manifest_base}({hls_format})'
    else:
      hls_manifest = f'{manifest_base}({hls_format},filter={filter_name})'

    print(f"The HLS (MP4) manifest URL is: {hls_manifest}")
    print("Open the following URL to playback the live stream in an HLS compliant player (HLS.js, Shaka, ExoPlayer) or directly in an iOS device")
    print({hls_manifest})
    print()

    dash_manifest = ""
    if filter_name is None:
      dash_manifest = f'{manifest_base}({dash_format})'
    else:
      dash_manifest = f'{manifest_base}({dash_format},filter={filter_name})'

    print(f"The DASH manifest URL is: {dash_manifest}")
    print("Open the following URL to playback the live stream from the LiveOutput in the Azure Media Player")
    print(f"https://ampdemo.azureedge.net/?url={dash_manifest}&heuristicprofile=lowlatency")
    print()
