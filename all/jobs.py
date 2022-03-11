#author: IngridAtMicrosoft

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.media import AzureMediaServices
import os

# Get environment variables
# After this call, environment variables can be referenced with os.getenv("NAMEOFVARIABLE")
load_dotenv()

# Get the default Azure credential from the environment variables AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENTANT_ID
default_credential = DefaultAzureCredential()

# The AMS Client
# From SDK
# AzureMediaServices(credentials, subscription_id, base_url=None)
client = AzureMediaServices(default_credential, os.getenv("SUBSCRIPTIONID"))

#To create a job, see the BasicEncoding sample in this repo.

#<JobDelete>
# Delete a job
# From the SDK
# delete(resource_group_name: str, account_name: str, transform_name: str, job_name: str, **kwargs: Any) -> None
# from azure.mgmt.media import AzureMediaServices
# Change myTransform to the name of the transform you that is associated with the job.
# Change myJob to the name of the job that you want to delete.

def deleteJob(resource_group_name,account_name,transform_name,job_name):
  client.jobs.delete(resource_group_name,account_name,transform_name,job_name)

deleteJob(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"),"myTransform","myJob")
#</JobDelete>

#<JobCancel>
# Cancel a job
# From the SDK
# cancel_job(resource_group_name: str, account_name: str, transform_name: str, job_name: str, **kwargs: Any) -> None
# Change tranformName to the name of the transform you that is associated with the job.
# Change jobName to the name of the job that you want to cancel.

def cancelJob(resource_group_name,account_name,transform_name,job_name):
  client.jobs.cancel_job(resource_group_name,account_name,transform_name,job_name)

cancelJob(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"),"transformName","jobName")
#</JobCancel>

#<JobGet>
# Get the details of a job
# From the SDK
# get(resource_group_name: str, account_name: str, transform_name: str, job_name: str, **kwargs: Any) -> _models.Job
# Change tranformName to the name of the transform you that is associated with the job.
# Change jobName to the name of the job that you want to get.

def getJob(resource_group_name,account_name,transform_name,job_name):
  client.jobs.get(resource_group_name,account_name,transform_name,job_name)

getJob(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"),"transformName","jobName")
#</JobGet>

#<JobList>
# List the jobs for a tranform
#list(resource_group_name: str, account_name: str, transform_name: str, filter: Optional[str] = None, orderby: Optional[str] = None, **kwargs: Any) -> Iterable['_models.JobCollection']
# Change tranformName to the name of the transform you for which you want a job list.

def listJobs(resource_group_name,account_name,transform_name):
  jobs = client.jobs.list(resource_group_name,account_name,transform_name)
  #Jobs returns all of the job objects which have properties such as name and state.
  for job in jobs:
    print("-----------JOB---------------")
    print("name: " , job.name)
    print("type: " , job.type)
    print("created: " , job.created)
    print("state: " , job.state)
    print("last_modified: " , job.last_modified)
    print("start_time: " , job.start_time)
    print("type: " , job.end_time)
    print("--------------------------")

listJobs(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"),"transformName")
#</JobList>

#<JobUpdate>
# Update is only supported for description and priority. 
# Updating priority will take effect when the Job state is Queued or Scheduled 
# and depending on the timing the priority update may be ignored.
# From the SDK
# update(resource_group_name: str, account_name: str, transform_name: str, job_name: str, parameters: "_models.Job", **kwargs: Any) -> _models.Job
# Change tranformName to the name of the transform you that is associated with the job
# Change jobName to the name of the job that you want to update.

# You don't necessarily have to pass a job object. You can pass JSON instead.

params = {
  "properties": {
    "description": "Take this job and love it.",
    "priority": "High"
  }
}

def updateJob(resource_group_name,account_name,transform_name,job_name,parameters):
  client.jobs.update(resource_group_name,account_name,transform_name,job_name,parameters)

updateJob(os.getenv("RESOURCEGROUP"),os.getenv("ACCOUNTNAME"),"transformName","jobName",params)
#</JobUpdate>