# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# This sample shows how to copy a section of a live event archive (output from the LiveOutput) to an MP4 file for use in downstream applications
# It is also useful to use this technique to get a file that you can submit to YouTube, Facebook, or other social platforms.
# The output from this can also be submitted to the Video Indexer service, which currently does not support ingest of AMS live archives
#
# The key concept to know in this sample is the VideoTrackDescriptor that allows you to extract a specific bitrate from a live archive ABR set.

import asyncio
from datetime import timedelta
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.media.aio import AzureMediaServices
from azure.mgmt.media.models import (
  Asset,
  Transform,
  TransformOutput,
  StandardEncoderPreset,
  CopyAudio,
  CopyVideo,
  Mp4Format,
  SelectVideoTrackByAttribute,
  TrackAttribute,
  AttributeFilter,
  FromAllInputFile,
  JobInputAsset,
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
name_prefix = "encode_copy_live"
output_folder = "Output/"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = str(random.randint(0,9999))

# Set this to the name of the Asset used in your LiveOutput. This would be the archived live event Asset name.
input_archive_name = "archiveAsset-3009"

transform_name = 'CopyLiveArchiveToMP4'

async def main():
  async with client:
    # Create a new Standard encoding Transform for H264
    print(f"Creating Standard Encoding transform named: {transform_name}")

    # For this snippet, we are using 'StandardEncoderPreset'
    transform_output = TransformOutput(
      preset=StandardEncoderPreset(
        codecs=[
          CopyAudio(),
          CopyVideo()
        ],
        filters={},
        # Specify the format for the output files - one for video+audio, and another for the thumbnails
        formats=[
          # Mux the H.264 video and AAC audio into MP4 files, using basename, label, bitrate and extension macros
          # Note that since you have multiple H264Layers defined above, you have to use a macro that produces unique names per H264Layer
          # Either {Label} or {Bitrate} should suffice
          Mp4Format(
            filename_pattern="Video-{Basename}-{Label}-{Bitrate}{Extension}"
          )
        ]
      ),
      # What should we do with the job if there is an error?
      on_error=OnErrorType.STOP_PROCESSING_JOB,
      # What is the relative priority of this job to others? Normal, high or low?
      relative_priority=Priority.NORMAL
    )

    print("Creating encoding transform...")

    # Adding transform details
    my_transform = Transform()
    my_transform.description="Built in preset using the Saas Copy Codec preset. This copies the source audio and video to an MP4 file"
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
    #<TopBitRate>
    # Use this to select the top bitrate from the live archive asset
    # The filter property allows you to select the "Top" bitrate which would be the
    # highest bitrate provided by the live encoder.
    video_track_selection = SelectVideoTrackByAttribute(
      attribute=TrackAttribute.BITRATE,
      filter=AttributeFilter.TOP    # Use this to select the top bitrate in this ABR asset for the job
    )
#</TopBitRate>
#<SubclipJobInput>
    # Create Job Input and Job Output Asset
    input = JobInputAsset(
      asset_name=input_archive_name,
      input_definitions=[
        FromAllInputFile(
          included_tracks=[
            video_track_selection   # Pass in the SelectVideoTrackByAttribute object created above to select only the top video.
          ]
        )
      ]
    )
#</SubclipJobInput>
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
