import os
from azure.devops.connection import Connection
from azure.devops.v6_0.work_item_tracking.models import JsonPatchOperation
from azure.devops.v6_0.work_item_tracking.models import WorkItemRelation
from azure.devops.v6_0.work_item_tracking.work_item_tracking_client import WorkItemTrackingClient
from msrest.authentication import BasicAuthentication

class Client:
    def __init__(self):
        self.feed_url = os.getenv("FEED_URL")
        self.ad_pat = os.getenv('AZURE_DEVOPS_PAT')
        self.ad_url = os.getenv('AZURE_DEVOPS_URL')
        self.ad_project = os.getenv('AZURE_DEVOPS_PROJECT')
        self.ad_epic_url = os.getenv('AZURE_DEVOPS_EPIC_URL')
        self.ad_area_path = os.getenv('AZURE_DEVOPS_AREA_PATH')
        self.ad_tags = os.getenv('AZURE_DEVOPS_TAGS')
        credentials = BasicAuthentication('', self.feed_url)
        connection = Connection(base_url=self.ad_url, creds=credentials)
        work_item_tracking_client = connection.clients.get_work_item_tracking_client()

    def set_field(self, document, field, value):
        document.append(JsonPatchOperation(
            from_=None,
            op="add",
            path=field,
            value=value))

    def create_work_item(self, parent_url: str, area_path: str, title: str, desc: str, tags: str,
                         item_type: str = "User Story"):
        document = []
        self.set_field(document, "/fields/System.Title", title)
        self.set_field(document, "/fields/System.AreaPath", area_path)
        self.set_field(document, "/fields/System.Description", desc)
        self.set_field(document, "/fields/System.Tags", tags)
        self.set_field(document, "/relations/-", WorkItemRelation(
            rel="System.LinkTypes.Hierarchy-Reverse",
            url=parent_url,
            attributes={
                "name": "Parent",
            }
        ))
        return self.create_work_item(document, self.ad_project, item_type)
