from fastapi import APIRouter, Request
from classifier.app.models.models import ReqClassifier
from classifier.app.service.classification import Classification
from classifier.log import get_logger
from classifier.app.daemon import server_version



logger = get_logger(__name__)
class APIv1:
    """
    Controller Class for all the api endpoints for App resource.
    """

    def __init__(self, prefix: str):
        self.router = APIRouter(prefix=prefix)

    @staticmethod
    def classify_data(data: ReqClassifier):
        # "/classify" API entrypoint
        # Execute entity/topic classification

        cls_obj = Classification(data.model_dump())
        response = cls_obj.process_request()
        return response

    @staticmethod
    def health(request: Request):
        return f"Entity Classifier Server version {server_version} is running"
    
