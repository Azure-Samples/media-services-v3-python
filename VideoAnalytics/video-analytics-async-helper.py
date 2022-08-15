import asyncio
from datetime import timedelta
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.media.aio import AzureMediaServices
from azure.mgmt.media.models import (
  VideoAnalyzerPreset,
  Transform,
  TransformOutput
  )
import os, random

# Import Job Helpers
from importlib.machinery import SourceFileLoader
mymodule = SourceFileLoader('encoding_job_helpers', '../../Common/Encoding/encoding_job_helpers.py').load_module()

# Get environment variables
load_dotenv()

# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
default_credential = DefaultAzureCredential()

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

# The file you want to upload.  For this example, the file is placed under Media folder. 
# The file ignite.mp4 has been provided for you. 
source_file = "ignite.mp4"
name_prefix = "analyze-video"
output_folder = "../../Output/"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "mySampleRandomID" + str(random.randint(0,9999))

transform_name = 'VideoAnalyzerTransform'

async def main():
  async with client:
    # Create a new Video Analyzer Transform Preset using the preset configuration
    video_transform_output = TransformOutput(
      preset = VideoAnalyzerPreset(
        audio_language = "en-US",   # Be sure to modify this to your desired language code in BCP-47 format
        insights_to_extract = "AllInsights",    # Video Analyzer can also run in Video only mode.
        mode = "Standard",    # Video analyzer can also process audio in basic or standard mode when using All Insights
        experimental_options = {  # Optional settings for preview or experimental features
          # "SpeechProfanityFilterMode = "None" " # Disables the speech-to-text profanity filtering
        }
      )
    )

    # Ensure that you have customized transforms for the VideoAnalyzer. This is really a one time setup operation.
    print("Creating Video Analyzer transform...")

    # Adding transform details
    my_transform = Transform()
    my_transform.description="A simple Video Analyzer Transform"
    my_transform.outputs = [video_transform_output]

    await client.transforms.create_or_update(resource_group, account_name, transform_name, my_transform)

    print(f"{transform_name} created (or updated if it existed already). ")
    print()
    
    input = await mymodule.get_job_input_type(source_file, {}, name_prefix, uniqueness)
    output_asset_name = f"{name_prefix}-output-{uniqueness}"
    job_name = f"{name_prefix}-job-{uniqueness}"
    
    print(f"Creating the output asset (container) to analyze the content into...")
    output_asset = await client.assets.create_or_update(resource_group, account_name, output_asset_name, {})
    if output_asset:
        print("Output Asset created.")
    else:
        print("There was a problem creating an output asset.")
    
    print() 
    print(f"Submitting the analyzer job to the {transform_name} job queue...")
    job = await mymodule.submit_job(transform_name, job_name, input, output_asset_name)
    
    print(f"Waiting for analyzer job - {job.name} - to finish analyzing")
    job = await mymodule.wait_for_job_to_finish(transform_name, job_name)
    
    if job.state == 'Finished':
      await mymodule.download_results(output_asset_name, output_folder)
      print("Downloaded results to local folder. Please review the outputs from the analysis job.")
    
  # closing media client
  print('Closing media client')
  await client.close()
    
  # closing credential client
  print('Closing credential client')
  await default_credential.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
