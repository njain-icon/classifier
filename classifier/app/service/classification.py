"""
Module for text classification
"""


import traceback

from pydantic import ValidationError

from classifier.app.models.models import ReqClassifier
from classifier.app.models.models import ClassifierJsonResponse
from classifier.app.models.models import AiDataModel
from classifier.entity_classifier.entity_classifier import EntityClassifier
from classifier.log import get_logger


logger = get_logger(__name__)

class Classification:
    """
    Classification wrapper class for Entity and Semantic classification with anonymization
    """

    def __init__(self, data: dict):
        self.input = data


    @staticmethod
    def _get_classifier_response(req: ReqClassifier):
        """
        Processes the input prompt through the entity classifier and anonymizer, and returns
        the resulting information encapsulated in an AiDataModel object.

        Returns:
            AiDataModel: An object containing the anonymized document, entities, and their counts.
        """
        doc_info = AiDataModel(
            data="",
            entityDetails={},
        )
        try:
            entity_classifier_obj = EntityClassifier(req.country_list)
            entity_details, input_text = entity_classifier_obj.entity_classifier_and_anonymizer(
                req.text, anonymize_snippets=req.anonymize
            )
            
            doc_info.entityDetails = entity_details
            if req.anonymize:
                doc_info.data = input_text
        except (KeyError, ValueError, RuntimeError) as e:
            logger.error(f"Failed to get classifier response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error:{e}\n{traceback.format_exc()}")
        return doc_info



    def process_request(self):
        """
        Processes the user request for classification and returns a structured response.

        Returns:
            ClassifierResponse: The response object containing classification results or error details.
        """
        try:
            req = ReqClassifier.model_validate(self.input)
            if not req.text:
                return ClassifierJsonResponse.build(
                    body={"error": "Input data is missing"}, status_code=400
                )
            doc_info = self._get_classifier_response(req)
            return ClassifierJsonResponse.build(
                body=doc_info.model_dump(exclude_none=True), status_code=200
            )
        except ValidationError as e:
            logger.error(
                f"Validation error in Classification API process_request:{e}\n{traceback.format_exc()}"
            )
            return ClassifierJsonResponse.build(
                body={"error": f"Validation error: {e}"}, status_code=400
            )
        except Exception:
            response = AiDataModel(
                data=None,
                entityDetails={}

            )
            logger.error(
                f"Error in Classification API process_request: {traceback.format_exc()}"
            )
            return ClassifierJsonResponse.build(
                body=response.model_dump(exclude_none=True), status_code=500
            )
