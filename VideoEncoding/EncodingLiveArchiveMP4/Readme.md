---
topic: sample
languages:
    - Python
products:
    - azure-media-services
description: "This sample demonstrates how to copy a section of a live event archive (output from the LiveOutput) to an MP4 file for use in downstream applications."
---

# Encode with a custom Transform copying a section of a live event archive

This sample demonstrates how to copy a section of a live event archive (output from the LiveOutput) to an MP4 file for use in downstream applications. It shows how to perform the following tasks:

* Creates a custom encoding transform (with custom Built-in Encoding configured)
* Creates a filter property to select the "Top" bitrate
* Creates an input asset that points to the live event archive to be packaged to MP4 format
* Submits a job and monitoring the job using polling method or Event Grid events
* Downloads the output asset

### .env

Use [sample.env](../../sample.env) as a template for the .env file to be created. The .env file must be placed at the root of the sample (same location than sample.env).
Connect to the Azure portal with your browser and go to your media services account / API access to get the .ENV data to store the .env file.