# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# This sample shows how to use the built-in Copy codec preset that can take a source video file that is already encoded
# using H264 and AAC audio, and copy it into MP4 tracks that are ready to be streamed by the AMS service.
# In addition, this preset generates a fast proxy MP4 from the source video.
# This is very helpful for scenarios where you want to make the uploaded MP4 asset available quickly for streaming, but also generate
# allow quality proxy version of the asset for quick preview, video thumbnails, or low bitrate delivery while your application logic
# decides if you need to backfill any more additional layers (540P, 360P, etc) to make the full adaptive bitrate set complete.
# This strategy is commonly used by services like YouTube to make content appear to be "instantly" available, but slowly fill in the
# quality levels for a more complete adaptive streaming experience. See the Encoding_BuiltIn_CopyCodec sample for a version that does not
# generate the additional proxy layer.
#
# This is useful for scenarios where you have complete control over the source asset, and can encode it in a way that is
# consistent with streaming (2-6 second GOP length, Constant Bitrate CBR encoding, no or limited B frames).
# This preset should be capable of converting a source 1 hour video into a streaming MP4 format in under 1 minute, as it is not
# doing any encoding - just re-packaging the content into MP4 files.
#
# NOTE: If the input has any B frames encoded, we occasionally can get the GOP boundaries that are off by 1 tick
#       which can cause some issues with adaptive switching.
#       This preset works up to 4K and 60fps content.

# NOTE: Make sure your streaming endpoint is running, or the videos won't play.


import asyncio
from datetime import timedelta
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.media.aio import AzureMediaServices
from azure.mgmt.media.models import (
  Transform,
  TransformOutput,
  BuiltInStandardEncoderPreset,
  OnErrorType,
  Priority
  )
import os, random

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
name_prefix = "encode_builtin_copycodec_withproxy"
output_folder = "Output/"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = str(random.randint(0,9999))

transform_name = 'CopyCodecWithProxy'

async def main():
  async with client:
    # Create a new Standard encoding Transform for H264
    print(f"Creating Standard Encoding transform named: {transform_name}")

    # For this snippet, we are using 'BuiltInStandardEncoderPreset'
    transform_output = TransformOutput(
      preset = BuiltInStandardEncoderPreset(
        # uses the built in SaaS copy codec preset, which copies source audio and video to MP4 tracks.
        # This also generates a fast proxy. See notes at top of this file on constraints and use case.
        preset_name="saasProxyCopyCodec"
      ),
      # What should we do with the job if there is an error?
      on_error=OnErrorType.STOP_PROCESSING_JOB,
      # What is the relative priority of this job to others? Normal, high or low?
      relative_priority=Priority.NORMAL
    )

    print("Creating encoding transform...")

    # Adding transform details
    my_transform = Transform()
    my_transform.description="Built in preset using the Saas Copy Codec preset. This copies the source audio and video to an MP4 file."
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
    locator_name = f"locator{uniqueness}"

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

    # Uncomment the below to download the resulting files
    """
    if job.state == 'Finished':
      await mymodule.download_results(output_asset_name, output_folder)
      print("Downloaded results to local folder. Please review the outputs from the encoding job.")
    """

    # Publish the output asset for streaming via HLS or DASH
    if output_asset is not None:
      locator = await mymodule.create_streaming_locator(output_asset_name, locator_name)
      if locator.name is not None:
        await mymodule.get_streaming_urls(locator.name)

  # closing media client
  print('Closing media client')
  await client.close()

  # closing credential client
  print('Closing credential client')
  await default_credential.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
