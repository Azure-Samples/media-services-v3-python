---
topic: sample
languages:
    - Python
products:
    - azure-media-services
description: "Encode with a custom Transform using Built-in Copy Codec onto the video"
---

# Encode with a custom Transform using Built-in Copy Codec onto the video

This sample shows how to encode a video using a custom encoding Transform settings. It shows how to perform the following tasks:

* Creates a custom encoding transform (with built-in copy codec configured)
* Creates an input asset and upload a media file into it
* Submits a job and monitoring the job using polling method or Event Grid events
* Downloads the output asset

### .env

Use [sample.env](../../sample.env) as a template for the .env file to be created. The .env file must be placed at the root of the sample (same location than sample.env).
Connect to the Azure portal with your browser and go to your media services account / API access to get the .ENV data to store the .env file.