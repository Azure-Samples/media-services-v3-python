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
  StandardEncoderPreset,
  H264Layer,
  AacAudio,
  H264Video,
  H264Complexity,
  PngImage,
  Mp4Format,
  PngLayer,
  PngFormat,
  AacAudioProfile,
  OnErrorType,
  Priority,
  HlsSettings,
  AssetTrack,
  AudioTrack
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
source_file = "ElephantsDream_H264_1000kbps_AAC_und_ch2_128kbps.mp4"
name_prefix = "audio-language-track-"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = str(random.randint(0,9999))

transform_name = 'H264Encoding'

async def main():
  async with client:
    print(f"Creating Standard Encoding transform named: {transform_name}")

    transform_output = TransformOutput(
      preset=StandardEncoderPreset(
        codecs=[
          AacAudio(
            channels=2,
            sampling_rate=48000,
            bitrate=128000,
            profile=AacAudioProfile.AAC_LC
          ),
          H264Video(
            key_frame_interval=timedelta(seconds=2),
            complexity=H264Complexity.BALANCED,
            layers=[
              H264Layer(
                bitrate=3600000,   # Units are in bits per second and not kbps or Mbps - 3.6Mbps or 3,600 kbps
                width=1200,
                height=720,
                buffer_window=timedelta(seconds=5),
                profile="Auto",
                label="HD-3600kbps"   # This label is used to modify the file name in the output formats
              ),
              H264Layer(
                bitrate=1600000,   # Units are in bits per second and not kbps or Mbps - 3.6Mbps or 3,600 kbps
                width= 960,
                height=540,
                buffer_window=timedelta(seconds=5),
                profile="Auto",
                label="SD-1600kbps"   # This label is used to modify the file name in the output formats
              ),
              H264Layer(
                bitrate=600000,   # Units are in bits per second and not kbps or Mbps - 3.6Mbps or 3,600 kbps
                width=640,
                height=480,
                buffer_window=timedelta(seconds=5),
                profile="Auto",
                label="SD-600kbps"   # This label is used to modify the file name in the output formats
              )
            ],
          ),
          PngImage(
            # Also generate a set of PNG thumbnails
            start="25%",
            step="25%",
            range="25%",
            layers=[
              PngLayer(
                width="50%",
                height="50%"
              )
            ]
          )
        ],
        # Specify the format for the output files - one for video+audio, and another for the thumbnails
        formats = [
          # Mux the H.264 video and AAC audio into MP4 files, using basename, label, bitrate and extension macros
          # Note that since you have multiple H264Layers defined above, you have to use a macro that produces unique names per H264Layer
          # Either {Label} or {Bitrate} should suffice
          Mp4Format(
            filename_pattern="Video-{Basename}-{Label}-{Bitrate}{Extension}"
          ),
          PngFormat(
            filename_pattern="Thumbnail-{Basename}-{Index}{Extension}"
          )
        ]
      ),
      on_error=OnErrorType.STOP_PROCESSING_JOB,
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
      print("Job is finished")
      ####### LATE BOUND AUDIO TRACK #######
      # This is the late bound audio track file we will upload to the asset container
      audio_filename= "ElephantsDream_audio_spa.mp4";
      #audio_folder = "elephants_dream";
      print("Uploading the Audio language file to the output asset.")
      # Get the SAS URL for the output asset.
      await mymodule.upload_file(asset_name=output_asset_name,input_file=audio_filename)
      # Update the tracks
      hls_settings = HlsSettings(default=False,forced=False)
      audio_track = AudioTrack(file_name=audio_filename,display_name="Spanish",language_code="es_Es",hls_settings=hls_settings)
      track = AssetTrack(track=audio_track)
      await mymodule.update_tracks(asset_name=output_asset_name, track_name="Spanish", parameters=track)


  # closing media client
  print('Closing media client')
  await client.close()

  # closing credential client
  print('Closing credential client')
  await default_credential.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
