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
  ContentKeyPolicySymmetricTokenKey,
  ContentKeyPolicyTokenRestriction,
  ContentKeyPolicyRestrictionTokenType,
  ContentKeyPolicyWidevineConfiguration,
  ContentKeyPolicyOption,
  ContentKeyPolicy,
  ContentKeyPolicyTokenClaim,
  StreamingLocator
  )
import os
import random
import base64
import time
import jwt
import json

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
name_prefix = "basicwidevine"
output_folder = "Output/"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = str(random.randint(0,9999))

############# BEGIN DRM #############
# Content protection variables
content_key_policy_name = 'CommonEncryptionCencDrmContentKeyPolicy_2021_12_15'
symmetric_key = os.getenv('DRMSYMMETRICKEY')
locator_name = f"locator{uniqueness}"

# DRM Configuration Settings
issuer = 'my_issuer'
audience = 'my_audience'

async def create_or_update_content_key_policy(policy_name,token_signing_key):
    # Create the content key policy that configures how the content key is delivered to end clients
    # via the Key Delivery component of Azure Media Services.
    # We are using the ContentKeyIndentifierClaim in the ContentKeyPolicy which means that the token presented
    # to the Key Delivery Component must have the identifier of the content key in it.
    print("Creating content key policy")

    primary_key = ContentKeyPolicySymmetricTokenKey(
        key_value=token_signing_key
    )

    required_claims = ContentKeyPolicyTokenClaim(
    # Add any number of custom claims that you may want to apply to your key policy here.
    # Example  1:
    # {
    #    claimType: "urn:microsoft:azure:mediaservices:maxuses"  // use this to require the max users claim
    # },
    # Example  2:
    # {
    #    claimType: "userProfile" // Require your own custom user profile claim type or whatever you want.
    # }
    )

    restriction = ContentKeyPolicyTokenRestriction(
        issuer=issuer,
        audience=audience,
        primary_verification_key=primary_key,
        restriction_token_type=ContentKeyPolicyRestrictionTokenType.JWT,
        alternate_verification_keys=None,
        required_claims=None
    )

    widevine_config = ContentKeyPolicyWidevineConfiguration(
        widevine_template=json.dumps(
            {
                "allowed_track_types": "SD_HD",
                "content_key_specs": [
                    {
                        "track_type": "SD",
                        "security_level": 1,
                        "required_output_protection": {
                            "HDCP": "HDCP_NONE"
                            # NOTE: the policy should be set to "HDCP_v1" (or greater) if you need to disable screen capture. The Widevine desktop
                            # browser CDM module only blocks screen capture when HDCP is enabled and the screen capture application is using
                            # Chromes screen capture APIs.
                        }
                    }
                ],
                "policy_overrides": {
                    "can_play": True,
                    "can_persist": False,
                    "can_renew": False
                    # Additional OPTIONAL settings in Widevine template, depending on your use case scenario
                    # license_duration_seconds: 604800,
                    # rental_duration_seconds: 2592000,
                    # playback_duration_seconds: 10800,
                    # renewal_recovery_duration_seconds: <renewal recovery duration in seconds>,
                    # renewal_server_url: "<renewal server url>",
                    # renewal_delay_seconds: <renewal delay>,
                    # renewal_retry_interval_seconds: <renewal retry interval>,
                    # renew_with_usage: <renew with usage>
                }
            }
        )
    )

    # Add the license type configurations for PlayReady to the policy
    options = [
        ContentKeyPolicyOption(
            configuration=widevine_config,
            restriction=restriction
        )
    ]

    create_content_policy = await client.content_key_policies.create_or_update(
        resource_group_name=resource_group,
        account_name=account_name,
        content_key_policy_name=content_key_policy_name,
        parameters=ContentKeyPolicy(
            description="Content Key Policy Widevine",
            options=options
        )
    )

# Publish the output asset for streaming via HLS or DASH
async def create_streaming_locator(output_asset_name,locator_name,content_key_policy_name):
    locator_name = f"locator-{uniqueness}"
    streaming_locator = StreamingLocator(asset_name=output_asset_name, streaming_policy_name="Predefined_MultiDrmCencStreaming", default_content_key_policy_name=content_key_policy_name)
    locator = await client.streaming_locators.create(
        resource_group_name=resource_group,
        account_name=account_name,
        streaming_locator_name=locator_name,
        parameters=streaming_locator
    )
    return locator

async def get_streaming_urls(locator_name, token):
    streaming_endpoint = await client.streaming_endpoints.get(resource_group_name=resource_group,account_name=account_name,streaming_endpoint_name="default")
    #paths = client.streaming_locators.list(resource_group_name=resource_group,account_name=account_name,locator_name=locator_name)
    paths = await client.streaming_locators.list_paths(resource_group_name=resource_group,account_name=account_name,streaming_locator_name=locator_name)
    for path in paths.streaming_paths:
        for format_path in path.paths:
            manifest_path = "https://" + streaming_endpoint.host_name + format_path
            print(manifest_path)
            print("IMPORTANT!! For all DRM Samples to work, you must use an HTTPS hosted player page.")
            print("For Widevine testing, please open the link in the Microsoft Edge Browser.")
            print(f"Click to playback in AMP player: https://ampdemo.azureedge.net/?url={manifest_path}&widevine=true&token=Bearer%20{token}")

async def get_token(issuer,audience,token_signing_key):
    start_date = int(time.time()) - (5*60)      # Get the current time and subtract 5 minutes, then return as a Unix timestamp
    end_date = int(time.time()) + (24*60*60)    # Expire the token in 1 day, return Unix timestamp
    claims = {
        "exp": end_date,
        "nbf" : start_date
    }
    jwt_token = jwt.encode(
        payload={
        "exp": end_date,
        "nbf": start_date,
        "iss": issuer,
        "aud": audience
        },
        key=token_signing_key,
        algorithm="HS256",
    )
    return jwt_token

########## END DRM ###################


# Transform settings
transform_name = 'H264Encoding'

async def main():
  async with client:
    # Create a new Standard encoding Transform for H264
    print(f"Creating Standard Encoding transform named: {transform_name}")

    # For this snippet, we are using 'StandardEncoderPreset'
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

    # Uncomment the below to download the resulting files.
    """
    if job.state == 'Finished':

      #await mymodule.download_results(output_asset_name, output_folder)
      #print("Downloaded results to local folder. Please review the outputs from the encoding job.")
    """

    if job.state == "Finished":
        # Set a token signing key that you want to use from the .env file
        # WARNING: This is an important secret when moving to a production system and should be kept in a Key Vault.
        token_signing_key = base64.b64decode(symmetric_key)

        await create_or_update_content_key_policy(content_key_policy_name,token_signing_key)

        locator = await create_streaming_locator(output_asset_name=output_asset_name,locator_name=locator_name,content_key_policy_name=content_key_policy_name)

        token = await get_token(issuer=issuer,audience=audience,token_signing_key=token_signing_key)

        print(f"The JWT token used is: {token}")
        print("You can decode the token using a tool like https://www.jsonwebtoken.io/ with the symmetric encryption key to view the decoded results.")

        if locator.name:
           urls = await get_streaming_urls(locator.name,token)
        else:
           print("Locator was not created or Locator.name is undefined")

  # closing media client
  print('Closing media client')
  await client.close()

  # closing credential client
  print('Closing credential client')
  await default_credential.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
