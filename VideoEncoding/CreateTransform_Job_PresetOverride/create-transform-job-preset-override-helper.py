
# This sample demonstrates how to create an very simple Transform to use for submitting any custom Job into.
# Creating a very basic transform in this fashion allows you to treat the AMS v3 API more like the legacy v2 API where
# transforms were not required, and you could submit any number of custom jobs to the same endpoint.
# In the new v3 API, the default workflow is to create a transform "template" that holds a unique queue of jobs just for that
# specific "recipe" of custom or pre-defined encoding.

# This sample shows how to create the blank empty Transform, and then submit a couple unique custom jobs to it,
# overriding the blank empty Transform.

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
  H265Video,
  H265Layer
  )
import os, random

# Import Job Helpers
from importlib.machinery import SourceFileLoader
mymodule = SourceFileLoader('encoding_job_helpers', '../../Common/Encoding/encoding_job_helpers.py').load_module()

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
name_prefix = "encodeH264"
output_folder = "../../Output/"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "mySampleRandomID" + str(random.randint(0,9999))

transform_name = 'EmptyTransform'

async def main():
  async with client:
    # Create a new Standard encoding Transform for H264
    print(f"Creating empty, blank, Standard Encoding transform named: {transform_name}")

    # In this sample, we create the simplest of Transforms allowed by the API to later submit custom jobs against.
    # Even though we define a single layer H264 preset here, we are going to override it later with a custom job level preset.
    # This allows you to treat this single Transform queue like the legacy v2 API, which only supported a single Job queue type.
    # In v3 API, the typical workflow that you will see in other samples is to create a transform "recipe" and submit jobs to it
    # that are all of the same type of output.
    # Some customers need the flexibility to submit custom Jobs.

    # First we create an mostly empty TransformOutput with a very basic H264 preset that we override later.
    # If a Job were submitted to this base Transform, the output would be a single MP4 video track at 1 Mbps.

    # For this snippet, we are using 'StandardEncoderPreset'
    transform_output = TransformOutput(
    preset = StandardEncoderPreset(
        codecs = [
            H264Video(layers = [H264Layer(bitrate = 1000000)])      # Units are in bits per second and not kbps or Mbps - 1 Mbps or 1,000 kbps
        ],
        # Specify the format for the output files - one for video+audio, and another for the thumbnails
        formats = [
        # Mux the H.264 video and AAC audio into MP4 files, using basename, label, bitrate and extension macros
        # Note that since you have multiple H264Layers defined above, you have to use a macro that produces unique names per H264Layer
        # Either {Label} or {Bitrate} should suffice
        Mp4Format(filename_pattern = "Video-{Basename}-{Label}-{Bitrate}{Extension}")
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
    my_transform.description="An empty transform to be used for submitting custom jobs against"
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
    print(f"Creating a new custom preset override and submitting the job to the empty transform {transform_name} job queue...")

    # Create a new Preset Override to define a custom standard encoding preset
    standard_preset_h264 = StandardEncoderPreset(
        codecs = [
            H264Video(
                # Next, add a H264Video for the video encoding
                key_frame_interval = timedelta(seconds=2),
                complexity = H264Complexity.SPEED,
                layers = [
                    H264Layer(
                        bitrate = 3600000,  # Units are in bits per second and not kbps or Mbps - 3.6 Mbps or 3,600 kbps
                        width = "1280",
                        height = "720",
                        label = "HD-3600kbps"   # This label is used to modify the file name in the output formats
                    )
                ]
            ),
            AacAudio(
                # Add an AAC Audio Layer for the audio encoding
                channels = 2,
                sampling_rate = 48000,
                bitrate = 128000,
                profile = AacAudioProfile.AAC_LC
            )
        ],
        formats = [
            Mp4Format(filename_pattern = "Video-{Basename}-{Label}-{Bitrate}{Extension}")
        ]
    )

    # Submit the H264 encoding custom job, passing in the preset override defined above.
    # print(f"Submitting the encoding job to the {transform_name} job queue...")
    job = await mymodule.submit_job(transform_name, job_name, input, output_asset_name, standard_preset_h264)

    # Next, we will create another preset override that uses HEVC instead and submit it against the same simple transform
    # Create a new Preset Override to define a custom standard encoding preset
    standard_preset_HEVC = StandardEncoderPreset(
        codecs = [
            H265Video(
                # Next, add a H265Video for the video encoding
                key_frame_interval = timedelta(seconds=2),
                complexity = H264Complexity.SPEED,
                layers = [
                    H265Layer(
                        bitrate = 1800000, # Units are in bits per second and not kbps or Mbps - 3.6 Mbps or 3,600 kbps
                        max_bitrate = 1800000,
                        width = "1280",
                        height = "720",
                        b_frames = 4,
                        label = "HD-1800kbps" # This label is used to modify the file name in the output formats
                    )
                ]
            ),
            AacAudio(
                # Add an AAC audio layer for the audio encoding
                channels = 2,
                sampling_rate = 48000,
                bitrate = 128000,
                profile = AacAudioProfile.AAC_LC
            )
        ],
        formats=[
            Mp4Format(filename_pattern = "Video-{Basename}-{Label}-{Bitrate}{Extension}")
        ]
    )

    # Let's update some names to re-use for the HEVC job we want to submit
    job_name_HEVC = job_name + '_HEVC'
    out_asset_name_HEVC = output_asset_name + '_HEVC'

    # Create a new output asset
    print(f"Creating a new output asset (container) to encode the content into...")
    output_asset2 = await client.assets.create_or_update(resource_group, account_name, out_asset_name_HEVC, {})
    if output_asset2:
        print("Output Asset created.")
    else:
        print("There was a problem creating an output asset.")

    # Submit the next HEVC custom job, passing in the preset override defined above.
    job2 = await mymodule.submit_job(transform_name, job_name_HEVC, input, out_asset_name_HEVC, standard_preset_HEVC)

    print(f"Waiting for encoding jobs to finish")
    job = await mymodule.wait_for_job_to_finish(transform_name, job_name)
    job2 = await mymodule.wait_for_job_to_finish(transform_name, job_name_HEVC)

    # Wait for the first H264 job to finish and then download the output
    if job.state == 'Finished':
      await mymodule.download_results(output_asset_name, output_folder)
      print("Downloaded results to local folder. Please review the outputs from the encoding job.")

    # Check on the status of the second HEVC encoding job and then download the output
    if job2.state == 'Finished':
      await mymodule.download_results(out_asset_name_HEVC, output_folder)
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
