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
  AacAudio,
  AacAudioProfile,
  H264Video,
  H264Complexity,
  H264Layer,
  Mp4Format,
  JobInputSequence,
  AbsoluteClipTime,
  Job,
  JobInputAsset,
  JobOutputAsset,
  OnErrorType,
  Priority,
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
bumper_file = "Azure_Bumper.mp4"
name_prefix = "stitchTwoAssets"
output_folder = "../../Output/"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "mySampleRandomID" + str(random.randint(0,9999))

transform_name = 'StitchTwoAssets'

async def main():
  async with client:
    # Create a new Standard encoding Transform for H264
    print(f"Creating Standard Encoding transform named: {transform_name}")

    # For this snippet, we are using 'StandardEncoderPreset'
    transform_output = TransformOutput(
      preset = StandardEncoderPreset(
        codecs = [AacAudio(channels=2, sampling_rate=48000, bitrate=128000, profile=AacAudioProfile.AAC_LC),
                  H264Video(key_frame_interval=timedelta(seconds=2), complexity=H264Complexity.BALANCED, layers=[H264Layer(bitrate=3600000, width="1280", height="720", label="HD-3600kbps")]),
        ],
        # Specify the format for the output files - one for video+audio, and another for the thumbnails
        formats = [
          # Mux the H.264 video and AAC audio into MP4 files, using basename, label, bitrate and extension macros
          # Note that since you have multiple H264Layers defined above, you have to use a macro that produces unique names per H264Layer
          # Either {Label} or {Bitrate} should suffice
          Mp4Format(filename_pattern="Video-{Basename}-{Label}-{Bitrate}{Extension}")
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
    my_transform.description="Stitches together two assets"
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

    # Asset names for main input and bumper input
    main_asset_name = f"main-{uniqueness}"
    bumper_asset_name = f"bumper-{uniqueness}"

    try:
      # Create a new Asset and upload the 1st specified local video file into it. This is our video "bumper" to stitch to the front.
      main_input = await mymodule.create_input_asset(main_asset_name, source_file)   # This creates and uploads the main video file

      # Create a second Asset and upload the 2nd specified local video file into it.
      bumper_input = await mymodule.create_input_asset(bumper_asset_name, bumper_file)     # This creates and uploads the second video file.
    except:
      raise ValueError("Error: Input assets were not created properly.")

    # Create a Job Input Sequence with the two assets to stitch together
    # In this sample, we will stitch a bumper into the main video asset at the head, 6 seconds, and at the tail. We end the main video at 12s total.
    # TIMELINE :   | Bumper | Main video -----> 6 s | Bumper | Main Video 6s -----------> 12s | Bumper |s
    # You can extend this sample to stitch any number of assets together and adjust the time offsets to create custom edits
    job_input_sequence = JobInputSequence(
      inputs=[
        # Start with the bumper video file
        JobInputAsset(
          asset_name=bumper_asset_name,
          files=[bumper_file],
          start=AbsoluteClipTime(time=timedelta(seconds=0)),
          label="bumper"
        ),
        # Cut to 6 seconds of the main video
        JobInputAsset(
          asset_name=main_asset_name,
          files=[source_file],
          start=AbsoluteClipTime(time=timedelta(seconds=0)),
          end=AbsoluteClipTime(time=timedelta(seconds=6)),
          label="main"
        ),
        # Mid-roll the bumper again just to annoy people...
        JobInputAsset(
          asset_name=bumper_asset_name,
          files=[bumper_file],
          start=AbsoluteClipTime(time=timedelta(seconds=0)),
          label="bumper"
        ),
        # Go back to main video for 6 seconds
        JobInputAsset(
          asset_name=main_asset_name,
          files=[source_file],
          start=AbsoluteClipTime(time=timedelta(seconds=6)),
          end=AbsoluteClipTime(time=timedelta(seconds=12)),
          label="main"
        ),
        # Post-roll the bumper again
        JobInputAsset(
          asset_name=bumper_asset_name,
          files=[bumper_file],
          start=AbsoluteClipTime(time=timedelta(seconds=0)),
          label="bumper"
        )
      ]
    )

    output_asset_name = f"{name_prefix}-output-{uniqueness}"
    job_name = f"{name_prefix}-job-{uniqueness}"

    # Create the Output Asset for the Job to write final results to.
    print(f"Creating the output asset (container) to encode the content into...")
    output_asset = await client.assets.create_or_update(resource_group, account_name, output_asset_name, {})
    if output_asset:
        print("Output Asset created.")
    else:
        print("There was a problem creating an output asset.")

    print()
    print(f"Submitting the encoding job to the {transform_name} job queue...")
    job = await mymodule.submit_job_with_input_sequence(transform_name, job_name, job_input_sequence, output_asset_name)

    print(f"Waiting for encoding job - {job.name} - to finish")
    job = await mymodule.wait_for_job_to_finish(transform_name, job_name)

    if job.state == 'Finished':
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
