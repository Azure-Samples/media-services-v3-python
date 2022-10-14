from datetime import timedelta
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
from azure.storage.blob import BlobServiceClient
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
  Filters,
  Rectangle,
  VideoOverlay,
  Job,
  JobInputs,
  JobInputAsset,
  JobOutputAsset,
  OnErrorType,
  Priority
  )
import os

#Timer for checking job progress
import time

#Get environment variables
load_dotenv()


default_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

# Get the environment variables SUBSCRIPTIONID, RESOURCEGROUP and ACCOUNTNAME
subscription_id = os.getenv('SUBSCRIPTIONID')
resource_group = os.getenv('RESOURCEGROUP')
account_name = os.getenv('ACCOUNTNAME')

# The file you want to upload.  For this example, the file is placed under Media folder.
# The file ignite.mp4 has been provided for you. 
source_file_location = os.chdir("../../Media/")
source_file = "ignite.mp4"

# This is a random string that will be added to the naming of things so that you don't have to keep doing this during testing
uniqueness = "encodeOverlayPng"

# Use the following PNG image to overlay on top of the video
overlay_file = "AzureMediaService.png"
overlay_label = "overlayCloud"

# Set the attributes of the input Asset using the random number
in_asset_name = 'inputassetName' + uniqueness
in_alternate_id = 'inputALTid' + uniqueness
in_description = 'inputdescription' + uniqueness

# Create an Asset object
# The asset_id will be used for the container parameter for the storage SDK after the asset is created by the AMS client.
in_asset = Asset(alternate_id=in_alternate_id, description=in_description)

# Create the JobInput for the PNG Image Overlay
overlay_asset_name = 'overlayassetName' + uniqueness
overlay_asset_alternate_id = 'inputALTid' + uniqueness
overlay_asset_description = 'inputdescription' + uniqueness

# Create an Asset object for PNG Image overlay
overlay_in_asset = Asset(alternate_id=overlay_asset_alternate_id, description=overlay_asset_description)

# Set the attributes of the output Asset using the random number
out_asset_name = 'outputassetName' + uniqueness
out_alternate_id = 'outputALTid' + uniqueness
out_description = 'outputdescription' + uniqueness

# Create Ouput Asset object
out_asset = Asset(alternate_id=out_alternate_id, description=out_description)

# The AMS Client
print("Creating AMS Client")
client = AzureMediaServices(default_credential, subscription_id)

# Create an input Asset
print(f"Creating input asset {in_asset_name}")
input_asset = client.assets.create_or_update(resource_group, account_name, in_asset_name, in_asset)

# An AMS asset is a container with a specific id that has "asset-" prepended to the GUID.
# So, you need to create the asset id to identify it as the container
# where Storage is to upload the video (as a block blob)
in_container = 'asset-' + input_asset.asset_id

# Create an Overlay input Asset
print(f"Creating input asset {overlay_asset_name}")
overlay_asset = client.assets.create_or_update(resource_group, account_name, overlay_asset_name, overlay_in_asset)

# # An AMS asset is a container with a specific id that has "asset-" prepended to the GUID.
# # So, you need to create the asset id to identify it as the container
# # where Storage is to upload the video (as a block blob)
overlay_container = 'asset-' + overlay_asset.asset_id

# create an output Asset
print(f"Creating output asset {out_asset_name}")
output_asset = client.assets.create_or_update(resource_group, account_name, out_asset_name, out_asset)

### Use the Storage SDK to upload the video ###
print(f"Uploading the file {source_file}")

blob_service_client = BlobServiceClient.from_connection_string(os.getenv('STORAGEACCOUNTCONNECTION'))
blob_client = blob_service_client.get_blob_client(in_container, source_file)
working_dir = os.getcwd()
print(f"Current working directory: {working_dir}")
upload_file_path = os.path.join(working_dir, source_file)

# WARNING: Depending on where you are launching the sample from, the path here could be off, and not include the BasicEncoding folder. 
# Adjust the path as needed depending on how you are launching this python sample file. 

# Upload the video to storage as a block blob
with open(upload_file_path, "rb") as data:
  blob_client.upload_blob(data)
  
### Use the Storage SDK to upload the Overlay file
print(f"Uploading the file {overlay_file}")

blob_service_client = BlobServiceClient.from_connection_string(os.getenv('STORAGEACCOUNTCONNECTION'))
blob_client = blob_service_client.get_blob_client(overlay_container, overlay_file)
working_dir = os.getcwd()
print(f"Current working directory: {working_dir}")
upload_file_path = os.path.join(working_dir, overlay_file)

# WARNING: Depending on where you are launching the sample from, the path here could be off, and not include the BasicEncoding folder. 
# Adjust the path as needed depending on how you are launching this python sample file. 

# Upload the video to storage as a block blob
with open(upload_file_path, "rb") as data:
  blob_client.upload_blob(data)

transform_name = 'H264EncodingOverlayImagePng'

# Create a new BuiltIn Standard encoding Transform for H264 ContentAware Constrained
print(f"Creating Standard Encoding transform named: {transform_name}")

# For this snippet, we are using 'StandardEncoderPreset' with Overlay Image
transform_output = TransformOutput(
  preset = StandardEncoderPreset(
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
            bitrate=3600000,
            width="1280",
            height="720",
            label="HD-3600kbps"
          ),
          H264Layer(
            bitrate=1600000,
            width="960",
            height="540",
            label="SD-1600kbps"
          )
        ]
      )
    ],
    # Specify the format for the output files - one for video + audio, and another for the thumbnails
    formats=[
      Mp4Format(filename_pattern="Video-{Basename}-{Label}-{Bitrate}{Extension}")
    ],
    filters=Filters(
      overlays=[
        VideoOverlay(
          input_label=overlay_label,          # same label that is used in the JobInput to identify which file in the asset is the actual overlay image .png file.
          position=Rectangle(left="10%", top="10%"),       # left and top position of the overlay in absolute pixel or percentage relative to the source video resolution.
          # You can also set the height and width of the rectangle to draw into, but there is known problem here. 
          # If you use % for the top and left (or any of these) you have to stick with % for all or you will get a job configuration Error 
          # Also, it can alter your aspect ratio when using percentages, so you have to know the source video size in relation to the source image to 
          # provide the proper image size.  Recommendation is to just use the right size image for the source video here and avoid passing in height and width for now. 
          # height: (if above is percentage based, this has to be also! Otherwise pixels are allowed. No mixing. )
          # width: (if above is percentage based, this has to be also! Otherwise pixels are allowed No mixing. )              
          opacity=0.75,                            # Sets the blending opacity value to make the image slightly transparent over the video
          start=timedelta(seconds=0),              # Start at beginning of the video
          fade_in_duration=timedelta(seconds=2),   # 2 second fade in
          fade_out_duration=timedelta(seconds=2),  # 2 second fade out
          end=timedelta(seconds=5)                 # end the fade out at 5 seconds on the timeline... fade will begin 2 seconds before this end time
        )
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
transform = client.transforms.create_or_update(
  resource_group_name=resource_group,
  account_name=account_name,
  transform_name=transform_name,
  parameters=my_transform)

print(f"{transform_name} created (or updated if it existed already). ")

job_name = 'MyEncodingH264OverlayImagePng'+ uniqueness
print(f"Creating Encoding264OverlayImagePng job {job_name}")
files = (source_file, overlay_file)

# Create Video Input Asset
job_video_input_asset = JobInputAsset(asset_name=in_asset_name)

job_input_overlay = JobInputAsset(
  asset_name=overlay_asset_name,
  label=overlay_label   # Order does not matter here, it is the "label" used on the Filter and the jobInput Overlay that is important!
)

# Create a list of job inputs - we will add both the video and overlay image assets here as the inputs to the job.
job_inputs=[   
    job_video_input_asset,
    job_input_overlay
]

# Create Job Output Asset
outputs = JobOutputAsset(asset_name=out_asset_name)

# Create Job object and then create Trasnform Job
the_job = Job(input=JobInputs(inputs=job_inputs), outputs=[outputs], correlation_data={ "propertyname": "string" })
job: Job = client.jobs.create(resource_group, account_name, transform_name, job_name, parameters=the_job)

# Check Job State
job_state = client.jobs.get(resource_group, account_name, transform_name, job_name)
# First check
print("First job check")
print(job_state.state)

# Check the state of the job every 10 seconds. Adjust time_in_seconds = <how often you want to check for job state>
def countdown(t):
    while t: 
        mins, secs = divmod(t, 60) 
        timer = '{:02d}:{:02d}'.format(mins, secs) 
        print(timer, end="\r") 
        time.sleep(1) 
        t -= 1
    job_current = client.jobs.get(resource_group, account_name, transform_name, job_name)
    if(job_current.state == "Finished"):
      print(job_current.state)
      # TODO: Download the output file using blob storage SDK
      return
    if(job_current.state == "Error"):
      print(job_current.state)
      # TODO: Provide Error details from Job through API
      return
    else:
      print(job_current.state)
      countdown(int(time_in_seconds))

time_in_seconds = 10
countdown(int(time_in_seconds))
