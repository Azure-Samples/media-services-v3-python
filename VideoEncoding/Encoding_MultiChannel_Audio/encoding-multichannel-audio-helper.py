import asyncio
from datetime import timedelta
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.media.aio import AzureMediaServices
from azure.mgmt.media.models import (
  Asset,
  Transform,
  TransformOutput,
  SelectAudioTrackById,
  ChannelMapping,
  InputFile,
  StandardEncoderPreset,
  AacAudio,
  AacAudioProfile,
  Mp4Format,
  OutputFile,
  Job,
  JobInputAsset,
  JobOutputAsset,
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

# Get the environment variables AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP and AZURE_MEDIA_SERVICES_ACCOUNT_NAME
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

# The file you want to upload.  For this example, put the file in the same folder as this script. 
# Provide a sample file with 8 discrete audio tracks as layout is defined above. Path is relative to the working directory for Python
source_file = "surround-audio.mp4"
name_prefix = "encodeH264_multi_channel"
output_folder = "../../Output/"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "mySampleRandomID" + str(random.randint(0,9999))

transform_name = 'Custom_AAC_MultiChannel_Surround'

async def main():
  async with client:
    # Create a new Standard encoding Transform for H264
    print(f"Creating Standard Encoding transform named: {transform_name}")

    # The multi-channel audio file should contain a stereo pair on tracks 1 and 2, followed by multi channel 5.1 discrete tracks in the following layout
    # 1. Left stereo
    # 2. Right stereo
    # 3. Left front surround
    # 4. Right front surround
    # 5. Center surround
    # 6. Low frequency
    # 7. Back left 
    # 8. Back right

    # The channel mapping support is limited to only outputting a single AAC stereo track, followed by a 5.1 audio AAC track in this sample.
    # The Transform we created outputs two tracks, the first track is mapped to the 2 stereo inputs followed by the 5.1 audio tracks.
    track_list = [
      SelectAudioTrackById(track_id = 0, channel_mapping = ChannelMapping.STEREO_LEFT),
      SelectAudioTrackById(track_id = 1, channel_mapping = ChannelMapping.STEREO_RIGHT),
      SelectAudioTrackById(track_id = 2, channel_mapping = ChannelMapping.FRONT_LEFT),
      SelectAudioTrackById(track_id = 3, channel_mapping = ChannelMapping.FRONT_RIGHT),
      SelectAudioTrackById(track_id = 4, channel_mapping = ChannelMapping.CENTER),
      SelectAudioTrackById(track_id = 5, channel_mapping = ChannelMapping.LOW_FREQUENCY_EFFECTS),
      SelectAudioTrackById(track_id = 6, channel_mapping = ChannelMapping.BACK_LEFT),
      SelectAudioTrackById(track_id = 7, channel_mapping = ChannelMapping.BACK_RIGHT)
    ]

    # Create an input definition passing in the source file name and the list of included track mappings from that source file we made above.
    input_definitions = [InputFile(filename=source_file, included_tracks=track_list)]

    # From SDK
    # TransformOutput(*, preset, on_error=None, relative_priority=None, **kwargs) -> None
    # For this snippet, we are using 'BuiltInStandardEncoderPreset'
    # Create a new Content Aware Encoding Preset using the Preset Configuration
    transform_output = TransformOutput(
      preset=StandardEncoderPreset(
        codecs=[AacAudio(channels=2, sampling_rate=48000, bitrate=128000, profile=AacAudioProfile.AAC_LC, label="stereo"),
                AacAudio(channels=6, sampling_rate=48000, bitrate=320000, profile=AacAudioProfile.AAC_LC, label="surround")
        ],
        # Specify the format for the output files - one for AAC audio outputs to MP4
        formats=[
          # Mux the AAC audio into MP4 files, using basename, label, bitrate and extension macros
          # Note that since you have multiple AAC outputs defined above, you have to use a macro that produces unique names per AAC Layer
          # Either {Label} or {Bitrate} should suffice
          # By creating outputFiles and assigning the labels we can control which output tracks are muxed into the Mp4 files
          # If you choose to mux both the stereo and surround tracks into a single MP4 output, you can remove the outputFiles and remove the second MP4 format object. 
          Mp4Format(filename_pattern="{Basename}-{Label}-{Bitrate}{Extension}", output_files=[OutputFile(labels=["stereo", "surround"])])
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
    my_transform.description="A custom multi-channel audio encoding preset"
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
    # NOTE: This call has been modified from previous samples in the repository to now take the list of Input Definitions instead of just the filename.
    # This passes in the IncludedTracks list to map during the Transform.
    job = await mymodule.submit_job_with_track_definitions(transform_name, job_name, input, output_asset_name, input_definitions)
    
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
