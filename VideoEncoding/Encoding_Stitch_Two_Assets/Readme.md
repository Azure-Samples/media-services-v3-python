---
topic: sample
languages:
    - Python
products:
    - azure-media-services
description: "This sample demonstrates how to set up a custom encoding job with stitching two assets."
---

# Encode with a custom Transform to stitch two assets

This sample shows how to encode a video using a custom encoding Transform settings. It shows how to perform the following tasks:

* Creates a custom encoding transform (with AAC Audio and H264 Video configured)
* Creates an input asset and upload a media file into it
* Creates another input asset and upload a media file into it
* Creates a job sequence where the bumper will be stitched to the main video asset.
* Submits a job and monitoring the job using polling method or Event Grid events
* Downloads the output asset

### .env

Use [sample.env](../../sample.env) as a template for the .env file to be created. The .env file must be placed at the root of the sample (same location than sample.env).
Connect to the Azure portal with your browser and go to your media services account / API access to get the .ENV data to store the .env file.