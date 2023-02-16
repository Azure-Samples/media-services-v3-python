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
  Filters,
  Mp4Format,
  VideoOverlay,
  JobInputAsset,
  Rectangle,
  AacAudioProfile,
  OnErrorType,
  Priority
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
name_prefix = "encodeOverlayPng"
output_folder = "../../Output/"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "mySampleRandomID" + str(random.randint(0,9999))

# Use the following PNG image to overlay on top of the video
overlay_file = "AzureMediaService.png"
overlay_label = "overlayCloud"
transform_name = 'H264EncodingOverlayImagePng'

async def main():
  async with client:
    # Create a new Standard encoding Transform for H264
    print(f"Creating Standard Encoding transform named: {transform_name}")

    # For this snippet, we are using 'StandardEncoderPreset'
    transform_output = TransformOutput(
      preset = StandardEncoderPreset(
        codecs=[AacAudio(channels=2, sampling_rate=48000, bitrate=128000, profile=AacAudioProfile.AAC_LC),
                H264Video(key_frame_interval=timedelta(seconds=2), complexity=H264Complexity.BALANCED,
                          layers=[H264Layer(bitrate=3600000, width="1280", height="720", label="HD-3600kbps"),
                                  H264Layer(bitrate=1600000, width="960", height="540", label="SD-1600kbps")]
                )
        ],
        # Specify the format for the output files - one for video + audio, and another for the thumbnails
        formats=[Mp4Format(filename_pattern="Video-{Basename}-{Label}-{Bitrate}{Extension}")],
        filters=Filters(overlays=[VideoOverlay(input_label=overlay_label,          # same label that is used in the JobInput to identify which file in the asset is the actual overlay image .png file.
                                              position=Rectangle(left="10%",       # left and top position of the overlay in absolute pixel or percentage relative to the source video resolution.
                                                                  top="10%"
                                                                  # You can also set the height and width of the rectangle to draw into, but there is known problem here.
                                                                  # If you use % for the top and left (or any of these) you have to stick with % for all or you will get a job configuration Error
                                                                  # Also, it can alter your aspect ratio when using percentages, so you have to know the source video size in relation to the source image to
                                                                  # provide the proper image size.  Recommendation is to just use the right size image for the source video here and avoid passing in height and width for now.
                                                                  # height: (if above is percentage based, this has to be also! Otherwise pixels are allowed. No mixing. )
                                                                  # width: (if above is percentage based, this has to be also! Otherwise pixels are allowed No mixing. )
                                                ),
                                              opacity=0.75,                            # Sets the blending opacity value to make the image slightly transparent over the video
                                              start=timedelta(seconds=0),              # Start at beginning of the video
                                              fade_in_duration=timedelta(seconds=2),   # 2 second fade in
                                              fade_out_duration=timedelta(seconds=2),  # 2 second fade out
                                              end=timedelta(seconds=5))                 # end the fade out at 5 seconds on the timeline... fade will begin 2 seconds before this end time
                        ]
        )
      ),
      # What should we do with the job if there is an error?
      on_error=OnErrorType.STOP_PROCESSING_JOB,
      # What is the relative priority of this job to others? Normal, high or low?
      relative_priority=Priority.NORMAL
    )

    print("Creating encoding transform...")

    # Adding transform details
    my_transform = Transform()
    my_transform.description="A simple custom H264 encoding transform that overlays a PNG image on the video source"
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

    job_video_input_asset = await mymodule.get_job_input_type(source_file, {}, name_prefix, uniqueness)
    output_asset_name = f"{name_prefix}-output-{uniqueness}"
    job_name = f"{name_prefix}-job-{uniqueness}"

    # Create the JobInput for the PNG Image overlay
    overlay_asset_name = f"{name_prefix}-overlay-{uniqueness}"
    await mymodule.create_input_asset(overlay_asset_name, overlay_file)
    job_input_overlay = JobInputAsset(
      asset_name=overlay_asset_name,
      label=overlay_label   # Order does not matter here, it is the "label" used on the Filter and the jobInput Overlay that is important!
    )

    print(f"Creating the output asset (container) to encode the content into...")
    output_asset = await client.assets.create_or_update(resource_group, account_name, output_asset_name, {})
    if output_asset:
        print("Output Asset created.")
    else:
        print("There was a problem creating an output asset.")

    # Create a list of job inputs - we will add both the video and overlay image assets here as the inputs to the job.
    job_inputs = [
        job_video_input_asset,
        job_input_overlay   # Order does not matter here, it is the "label" used on the Filter and the job_input_overlay that is important!
    ]

    print()
    print(f"Submitting the encoding job to the {transform_name} job queue...")
    job = await mymodule.submit_job_multi_inputs(transform_name, job_name, job_inputs, output_asset_name)

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
