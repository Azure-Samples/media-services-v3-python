---
page_type: sample
languages:
- python
products:
- azure
- azure-media-services
name: Azure Media Services v3 Python Samples
description: "This repository contains samples showing how to use Azure Media Services v3 API using Python"
urlFragment: media-services-v3-python
lastModified: 3/1/2023
---

# Azure Media Services v3 Python Samples

**IMPORTANT NOTE : Azure Media Services have been retired on June 30, 2024. Please see the [retirement guide](https://learn.microsoft.com/azure/media-services/latest/azure-media-services-retirement).**

The samples in this repo are part of [Azure Media Services](https://media.microsoft.com).
Use this set of samples to get started with the Azure Media Service v3 API and Python client SDK.

**NOTE**
Owned and maintained by Microsoft. Please do not push changes directly to this repo.  Please fork the repo and set it as upstream and your own fork as origin. See the CONTRIBUTING.md file for more details.

## Getting Started

### Prerequisites

- If you don't have an Azure subscription, create a [free account](https://azure.microsoft.com/free/?WT.mc_id=A261C142F) before you begin.
- Create a resource group to use with these samples.
- Install Python 3.x

#### Use Python virtual environments

For every sample, we recommend that you always create and activate a virtual environment using the following steps:

1. Open the sample folder in VSCode or other editor
1. Create the virtual environment

``` bash
# py -3 uses the global python interpreter. You can also use python -m venv .venv.
py -3 -m venv .venv
```

This command runs the Python venv module and creates a virtual environment in a folder named .venv.

1. Activate the virtual environment:

``` bash
.venv\scripts\activate
```

A virtual environment is a folder within a project that isolates a copy of a specific Python interpreter. Once you activate that environment (which Visual Studio Code does automatically), running pip install installs a library into that environment only. When you then run your Python code, it runs in the environment's exact context with specific versions of every library. And when you run pip freeze, you get the exact list of the those libraries. (In many of the samples, you create a requirements.txt file for the libraries you need, then use pip install -r requirements.txt. A requirements file is generally needed when you deploy code to Azure.)

### Installation

Set up and [configure your local Python dev environment for Azure](https://docs.microsoft.com/en-us/azure/developer/python/configure-local-development-environment)

Install the azure-identity library for Python. This module is needed for Azure Active Directory authentication. See the details at [Azure Identity client library for Python](https://docs.microsoft.com//python/api/overview/azure/identity-readme?view=azure-python#environment-variables)

``` bash
pip install azure-identity
```

Install the Python SDK for [Azure Media Services](https://docs.microsoft.com/python/api/overview/azure/media-services?view=azure-python)

The Pypi page for the Media Services Python SDK with latest version details is located at - [azure-mgmt-media](https://pypi.org/project/azure-mgmt-media/)

``` bash
pip install azure-mgmt-media
```

Install the [Azure Storage SDK for Python](https://pypi.org/project/azure-storage-blob/)

``` bash
pip install azure-storage-blob
```

``` bash
pip install azure-mgmt-storage
```

You can optionally install ALL of the requirements for a given samples by using the "requirements.txt" file in the samples folder

``` bash
pip install -r requirements.txt
```

You can also use pip to uninstall libraries and install specific versions, including preview versions. For more information, see [How to install Azure library packages for Python](https://docs.microsoft.com/azure/developer/python/azure-sdk-install).

## Create the .env file

Copy the contents from the sample.env file that is in your forked repo in the root folder. Then, create your own .env file by clicking on Add file -> Create new file. Name the file *.env* and fill in the variables.

Do not allow this .env file to be checked into your fork of the GitHub repository! This is disallowed in the .gitignore file, but be extra careful not to allow the credentials to leak into your source control for this file.

All samples will load the root ".env" file first, and some of the samples add additional .env variables needed for the samples to work inside each sample folder. Make sure to check each sample for additional environment settings that are required.


## Resources

- See the Azure Media Services [management API](https://docs.microsoft.com/python/api/overview/azure/mediaservices/management?view=azure-python).
- Learn how to use the [Storage APIs with Python](https://docs.microsoft.com/azure/developer/python/azure-sdk-example-storage-use?tabs=cmd)
- Learn more about the [Azure Identity client library for Python](https://docs.microsoft.com//python/api/overview/azure/identity-readme?view=azure-python#environment-variables)
- Learn more about [Azure Media Services v3](https://docs.microsoft.com/azure/media-services/latest/media-services-overview).
- Learn about the [Azure Python SDKs](https://docs.microsoft.com/azure/developer/python)
- Learn more about [usage patterns for Azure Python SDKs](https://docs.microsoft.com/azure/developer/python/azure-sdk-library-usage-patterns)
- Find more Azure Python SDKs in the [Azure Python SDK index](https://docs.microsoft.com/azure/developer/python/azure-sdk-library-package-index)
- [Azure Storage Blob Python SDK reference](https://docs.microsoft.com/python/api/azure-storage-blob/?view=azure-python)
