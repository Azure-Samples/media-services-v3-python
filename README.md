# Azure Media Services v3 Python Samples

Use this set of samples to get started with Azure Media Service v3 and Python.

**NOTE**
Owned and maintained by Microsoft. Please do not push changes directly to this repo.  Please fork the repo and set it as upstream and your own fork as origin. See the CONTRIBUTING.md file for more details.

## Features

This project framework provides the following features:

| Sample | Description |
|--------|-------------|
|[Basic encoding](/BasicEncoding/)| Basic example for uploading a local file or encoding from a source URL. Sample shows how to use storage SDK to download content, and shows how to stream to a player |
|[Face Redaction using events and functions](/FaceRedactorEventBased/)| This is an example of an event-based approach that triggers an Azure Media Services Face Redactor job on a video as soon as it lands on an Azure Storage Account. It leverages Azure Media Services, Azure Function, Event Grid and Azure Storage for the solution. For the full description of the solution, see the [README.md](https://github.com/Azure-Samples/media-services-v3-python/blob/main/VideoAnalytics/FaceRedactorEventBased/README.md)|

## Getting Started

### Prerequisites

* Install Python 3.x
* Install the Python SDK for [Azure Media Services](https://docs.microsoft.com/en-us/python/api/overview/azure/media-services?view=azure-python)

### Installation

Install the modules required by the scripts as shown in the *import* section of the samples. For example:

pip install adal

This module is needed for Azure Active Directory authentication.

## Resources

See the Azure Media Services [management API](https://docs.microsoft.com/en-us/python/api/overview/azure/mediaservices/management?view=azure-python).

Learn more about [Azure Media Services v3](https://docs.microsoft.com/en-us/azure/media-services/latest/media-services-overview).
