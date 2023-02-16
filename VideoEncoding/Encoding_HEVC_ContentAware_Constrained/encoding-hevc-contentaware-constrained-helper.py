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
  BuiltInStandardEncoderPreset,
  PresetConfigurations,
  EncoderNamedPreset,
  InterleaveOutput,
  OnErrorType,
  Priority
  )
import os, random

# Import Job Helpers
from importlib.machinery import SourceFileLoader
mymodule = SourceFileLoader('encoding_job_helpers', 'Common/encoding_job_helpers.py').load_module()

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
name_prefix = "contentAwareHEVCConstrained"
output_folder = "Output/"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = str(random.randint(0,9999))

transform_name = 'HEVCEncodingContentAwareConstrained'

async def main():
  async with client:
    # Create a new Standard encoding Transform for H264
    print(f"Creating Standard Encoding transform named: {transform_name}")

    # This sample uses constraints on the CAE encoding preset to reduce the number of tracks output and resolutions to a specific range.
    # First we will create a PresetConfigurations object to define the constraints that we want to use
    # This allows you to configure the encoder settings to control the balance between speed and quality. Example: set Complexity as Speed for faster encoding but less compression efficiency.

    preset_config = PresetConfigurations(
        complexity="Speed",
        # The output includes both audio and video.
        interleave_output=InterleaveOutput.INTERLEAVED_OUTPUT,
        # The key frame interval in seconds. Example: set as 2 to reduce the playback buffering for some players.
        key_frame_interval_in_seconds= 2,
        # The maximum bitrate in bits per second (threshold for the top video layer). Example: set max_bitrate_bps as 6000000 to avoid producing very high bitrate outputs for contents with high complexity
        max_bitrate_bps= 3000000,
        # The minimum bitrate in bits per second (threshold for the bottom video layer). Example: set min_bitrate_bps as 200000 to have a bottom layer that covers users with low network bandwidth.
        min_bitrate_bps= 200000,
        #The maximum height of output video layers. Example: set max_height as 720 to produce output layers up to 720P even if the input is 4K.
        max_height= 720,
        # The minimum height of output video layers. Example: set min_height as 360 to avoid output layers of smaller resolutions like 180P.
        min_height=270,
        #  The maximum number of output video layers. Example: set max_layers as 4 to make sure at most 4 output layers are produced to control the overall cost of the encoding job.
        max_layers=3
    )

    # From SDK
    # TransformOutput(*, preset, on_error=None, relative_priority=None, **kwargs) -> None
    # For this snippet, we are using 'BuiltInStandardEncoderPreset'
    # Create a new Content Aware Encoding Preset using the Preset Configuration
    transform_output = TransformOutput(
      preset = BuiltInStandardEncoderPreset(
        preset_name = EncoderNamedPreset.H265_CONTENT_AWARE_ENCODING,
        # Configurations can be used to control values used by the Content Aware Encoding Preset.
        configurations = preset_config
      ),
      # What should we do with the job if there is an error?
      on_error=OnErrorType.STOP_PROCESSING_JOB,
      # What is the relative priority of this job to others? Normal, high or low?
      relative_priority=Priority.NORMAL
    )

    print("Creating encoding transform...")

    # Adding transform details
    my_transform = Transform()
    my_transform.description="HEVC content aware encoding with configuration settings"
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

    # Uncomment the following lines to download the resulting files.
    """
    if job.state == 'Finished':
      await mymodule.download_results(output_asset_name, output_folder)
      print("Downloaded results to local folder. Please review the outputs from the encoding job.")
    """

  # closing media client
  print('Closing media client')
  await client.close()

  # closing credential client
  print('Closing credential client')
  await default_credential.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
