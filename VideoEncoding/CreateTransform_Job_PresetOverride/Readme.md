---
topic: sample
languages:
    - Python
products:
    - azure-media-services
description: "This sample demonstrates how to set up a custom encoding job that can override a preset top of your video during encoding."
---

# Encode with a custom Transform and preset override onto the video

This sample shows how to override a preset on a video using a custom encoding Transform settings. It shows how to perform the following tasks:

* Creates a custom encoding transform (with H264 Layer and MP4 configured)
* Creates an input asset and upload a media file into it
* Creates a new Preset Override to define a custom standard encoding preset
* Submits a job and monitoring the job using polling method or Event Grid events
* Creates another preset override that uses HEVC instead and submit it against the same simple transform
* Downloads the output asset

### .env

Use [sample.env](../../sample.env) as a template for the .env file to be created. The .env file must be placed at the root of the sample (same location than sample.env).
Connect to the Azure portal with your browser and go to your media services account / API access to get the .ENV data to store the .env file.