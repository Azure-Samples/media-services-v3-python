# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from datetime import timedelta
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.media.aio import AzureMediaServices
from azure.mgmt.media.models import (
  Transform,
  TransformOutput,
  AudioAnalyzerPreset,
  AudioAnalysisMode,
  OnErrorType,
  Priority
  )
import os
import random

# Import Job Helpers
from importlib.machinery import SourceFileLoader


mymodule = SourceFileLoader("encoding_job_helpers", "Common/encoding_job_helpers.py").load_module()


# Get environment variables
load_dotenv()


default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

# Get the environment variables
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
resource_group = os.getenv('AZURE_RESOURCE_GROUP')
account_name = os.getenv('AZURE_MEDIA_SERVICES_ACCOUNT_NAME')

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)

# Send envs to helper function
mymodule.set_account_name(account_name)
mymodule.set_resource_group(resource_group)
mymodule.set_subscription_id(subscription_id)
mymodule.create_default_azure_credential(default_credential)
mymodule.create_azure_media_services(client)

# The file you want to upload.  For this example, the file is placed under Media folder.
# The file ignite.mp4 has been provided for you.
source_file = "ignite.mp4"
name_prefix = "audioanalytics"
output_folder = "Output/"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = str(random.randint(0,9999))

transform_name = 'AudioAnalyzerTransformBasic'

async def main():
  async with client:
    # Create a new Standard encoding Transform for H264
    print(f"Creating Standard Encoding transform named: {transform_name}")

    # For this snippet, we are using 'AudioAnalyzerPreset'
    transform_output = TransformOutput(
    preset=AudioAnalyzerPreset(
        audio_language="en-GB",   # Be sure to modify this to your desired language code in BCP-47 format.
        # Set the language to British English - see see https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#speech-to-text

        # There are two modes available, Basic and Standard
        # Basic : This mode performs speech-to-text transcription and generation of a VTT subtitle/caption file.
        #         The output of this mode includes an Insights JSON file including only the keywords, transcription, and timing information.
        #         Automatic language detection and speaker diarization are not included in this mode.
        # Standard : Performs all operations included in the Basic mode, additionally performing language detection and speaker diarization.
        mode=AudioAnalysisMode.BASIC    # Change this to Standard if you would like to use the more advanced audio analyzer
    ),
    # What should we do with the job if there is an error?
    on_error=OnErrorType.STOP_PROCESSING_JOB,
    # What is the relative priority of this job to others? Normal, high or low?
    relative_priority=Priority.NORMAL
    )

    print("Creating encoding transform...")

    # Adding transform details
    my_transform = Transform()
    my_transform.description="A simple custom H264 encoding transform with 3 MP4 bitrates"
    my_transform.outputs = [transform_output]

    print(f"Creating transform {transform_name}")
    try:
      await client.transforms.create_or_update(
        resource_group_name=resource_group,
        account_name=account_name,
        transform_name=transform_name,
        parameters=my_transform)
      print(f"{transform_name} created (or updated if it existed already). ")
      print()
    except:
      print("There was an error creating the transform.")

    input = await mymodule.get_job_input_type(source_file, {}, name_prefix, uniqueness)
    output_asset_name = f"{name_prefix}-output-{uniqueness}"
    job_name = f"{name_prefix}-job-{uniqueness}"

    print(f"Creating the output asset (container) to encode the content into...")
    output_asset = await client.assets.create_or_update(resource_group, account_name, output_asset_name, {})
    if output_asset:
        print("Output Asset created.")
    else:
        print("There was a problem creating an output asset.")

    print()
    print(f"Submitting the encoding job to the {transform_name} job queue...")
    job = await mymodule.submit_job(transform_name, job_name, input, output_asset_name)

    print(f"Waiting for encoding job - {job.name} - to finish")
    job = await mymodule.wait_for_job_to_finish(transform_name, job_name)

    if job.state == 'Finished':
      # Download the resulting files: insights.json, metadata.json, transcript.ttml and transript.vtt
      await mymodule.download_results(output_asset_name, output_folder)
      print("Downloaded results to local folder. Please review the outputs from the encoding job.")

  # closing media client
  print('Closing media client')
  await client.close()

  # closing credential client
  print('Closing credential client')
  await default_credential.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
