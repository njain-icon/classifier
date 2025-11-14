from __future__ import annotations

from typing import List, Optional, Tuple

from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer import RecognizerResult

from classifier.entity_classifier.utils.judge_entity import judge_results
from classifier.entity_classifier.utils.result_validation import validate_extracted_data, is_not_part_of_decimal
# Note: legacy get_entities not used in YAML-driven v2 aggregation
from classifier.log import get_logger
from classifier.text_generation.text_generation import TextGeneration

from classifier.entity_classifier.core.loader import load_country_config
from classifier.entity_classifier.core.validation import ValidationProvider
from classifier.entity_classifier.engine.analyzer_factory import build_country_recognizer, build_engine_from_configs



logger = get_logger(__name__)


class EntityClassifier:
    """YAML-driven entity classifier.

    - Uses YAML configs and `BaseCountryAnalyzer` for detection (Presidio builtin+regex + LLM detect/validate)
    - Keeps judge (LLM) and anonymizer flow identical to v1
    - Maps YAML entity ids (e.g., 'us-ssn') to enum names (e.g., 'US_SSN') for downstream compatibility
    
    Args:
        countries: Optional list of country codes; defaults to environment config.
    """

    def __init__(self, countries: Optional[List[str]] = None):
        # Multi-country support via env or constructor
        self.countries = countries
        self.text_gen_obj = TextGeneration()
        self.anonymizer = AnonymizerEngine()
        self._group_conf: dict[str, tuple[float, str]] = {}
        self._display_name: dict[str, str] = {}
        self._target_entities: set[str] = set()
        self._validator_index: dict[str, dict] = {}
        self._validator = ValidationProvider()
        
        # Analyzer will be created in custom_analyze with a clean registry (no predefined recognizers)
        self._base_dir = None
        self.custom_analyze()
            
    # Function to check if two entities overlap based on their start and end positions
    def entities_overlap(self, entity1: RecognizerResult, entity2: RecognizerResult) -> bool:
        return not (entity1.end <= entity2.start or entity2.end <= entity1.start and entity1.entity_type != entity2.entity_type)

    
    def custom_analyze(self):
        # Always register YAML-driven country recognizers
        if not self.countries:
            self.countries = ["US"]

        # Create a fresh registry without predefined recognizers
        # Build analyzer with the clean registry

        countries_config = [load_country_config(country, base_dir=self._base_dir) for country in self.countries]

        self.analyzer = build_engine_from_configs(countries_config)

        for country in self.countries:
            try:
                cfg = load_country_config(country, base_dir=self._base_dir)
                recognizer = build_country_recognizer(cfg)
                self.analyzer.registry.add_recognizer(recognizer)
                # Track enabled YAML entity ids to restrict analyze targets
                for ent_id, ent in (cfg.entities or {}).items():
                    if ent.enabled and ent.detect and any(m in ent.detect.methods for m in ("regex", "llm")):
                        self._target_entities.add(ent_id)
                    # Build group/conf mapping from YAML
                    if ent.enabled:
                        min_conf = 1.0
                        try:
                            if ent.detect and ent.detect.thresholds and ent.detect.thresholds.min_confidence is not None:
                                min_conf = float(ent.detect.thresholds.min_confidence)
                        except Exception:
                            min_conf = 1.0
                        group_name = ent.group if getattr(ent, "group", None) else "unknown"
                        self._group_conf[ent_id] = (min_conf, group_name)
                        # Display name override
                        if getattr(ent, "return_name", None):
                            self._display_name[ent_id] = ent.return_name
                        # Validator index (YAML id -> {country, fn, rules})
                        vfn = getattr(ent, "validate_fn", None) or (ent.validation.fn if getattr(ent, "validation", None) else None)
                        vrules = (ent.validation.rules if getattr(ent, "validation", None) else {}) or {}
                        if vfn:
                            self._validator_index[ent_id] = {"country": country, "fn": vfn, "rules": vrules}

            except Exception as e:
                logger.warning(f"Failed to register country recognizer for {country}: {e}")

    def analyze_response(
        self, input_text: str, anonymize_all_entities: bool = True
    ) -> list[RecognizerResult]:
        """Run detection, validation, and overlap resolution for the supplied text.

        Args:
            input_text: Raw text to classify.
            anonymize_all_entities: Unused legacy flag (kept for signature compatibility).

        Returns:
            List of deduplicated ``RecognizerResult`` objects.

        Failure Modes:
            Logs and skips entities when validator functions raise. If detection raises,
            the exception is logged and processing continues for remaining entities.
        """
        # Detect via YAML-driven analyzer (single or multi-country)

        #entities = sorted(self._target_entities) if self._target_entities else None
        analyzer_results = self.analyzer.analyze(text=input_text, language="en")
        logger.info(f"analyzer_results {analyzer_results}")
        # Initialize outputs
        non_overlapping_results: List[RecognizerResult] = []
        overlapping_results: List[Tuple[RecognizerResult, ...]] = []
        current_overlap_group: List[RecognizerResult] = []
        # Sort entities by start position
        sorted_analyzer_results = sorted(analyzer_results, key=lambda x: x.start)
        for entity in sorted_analyzer_results:
            try:
                if is_not_part_of_decimal(entity.entity_type, input_text, entity.start, entity.end):
                    # Use YAML-driven mapping built at init; skip entities without a known group
                    min_conf, _group = self._group_conf.get(entity.entity_type, (0.0, "unknown"))
                    if _group == "unknown":
                        continue
                    # Apply YAML validator (if present) along with existing validate_extracted_data
                    value = input_text[entity.start: entity.end]
                    vinfo = self._validator_index.get(entity.entity_type)
                    yaml_valid = True
                    if vinfo and vinfo.get("fn"):
                        yaml_valid = self._validator.validate(
                            fn=vinfo["fn"],
                            value=value,
                            text=input_text,
                            country=vinfo.get("country") or "",
                            rules=vinfo.get("rules") or {},
                        )
                    if (
                        entity.score
                        and entity.score >= float(min_conf)
                        and validate_extracted_data(entity.entity_type, value, input_text)
                        and yaml_valid
                    ):
                        if current_overlap_group and self.entities_overlap(
                            current_overlap_group[-1], entity
                        ):
                            last_entity = current_overlap_group[-1]
                            if last_entity.entity_type == entity.entity_type:
                                non_overlapping_results.append(entity)
                            else:
                                current_overlap_group.append(entity)
                        else:
                            if len(current_overlap_group) > 1:
                                overlapping_results.append(tuple(current_overlap_group))
                            elif len(current_overlap_group) == 1:
                                non_overlapping_results.append(current_overlap_group[0])
                            current_overlap_group = [entity]
            except Exception as ex:
                import traceback
                logger.warning(
                    f"Error in analyze_response in entity classification v2. {str(ex)}"
                )
                logger.warning(traceback.format_exc())

        if len(current_overlap_group) > 1:
            overlapping_results.append(tuple(current_overlap_group))
        elif len(current_overlap_group) == 1:
            non_overlapping_results.append(current_overlap_group[0])
        overlapping_results_new = judge_results(
            input_text, overlapping_results, self.text_gen_obj
        )
        non_overlapping_results.extend(overlapping_results_new)
        return list(set(non_overlapping_results))

    def anonymize_response(
        self, analyzer_results: list, input_text: str
    ) -> tuple[list, str]:
        """Anonymize text using detected analyzer results.

        Args:
            analyzer_results: Recognizer results to anonymize.
            input_text: Original text.

        Returns:
            Tuple of (anonymized items, anonymized text string).

        Failure Modes:
            Propagates exceptions from the Presidio anonymizer; caller handles.
        """
        anonymized_text = self.anonymizer.anonymize(
            text=input_text, analyzer_results=analyzer_results
        )
        return anonymized_text.items, anonymized_text.text

    def _sort_analyzed_data(self, data: list) -> list:
        analyzed_data = [
            {
                "entity_type": entry.entity_type,
                "start": entry.start,
                "end": entry.end,
                "score": entry.score,
            }
            for entry in data
        ]
        analyzed_data.sort(key=lambda x: x["start"])
        return analyzed_data

    @staticmethod
    def _sort_anonymized_data(data: list) -> list:
        anonymized_data = [
            {"entity_type": entry.entity_type, "start": entry.start, "end": entry.end}
            for entry in data
        ]
        anonymized_data.sort(key=lambda x: x["start"])
        return anonymized_data

    @staticmethod
    def update_anonymized_location(
        start: int, end: int, location_count: int
    ) -> tuple[str, int]:
        location = f"{start+location_count}_{end+location_count+6}"
        location_count += 6
        return location, location_count

    def get_analyzed_entities_response(
        self, data: list, anonymized_response: list = None, input_text: str = None
    ) -> list:
        """Convert recognizer results into API-ready payload.

        Args:
            data: Recognizer results.
            anonymized_response: Optional anonymized entries to align locations.

        Returns:
            List of dictionaries containing entity metadata.

        Failure Modes:
            Logs exceptions per-entity and skips malformed entries.
        """
        analyzed_data = self._sort_analyzed_data(data)
        if anonymized_response:
            anonymized_response = self._sort_anonymized_data(anonymized_response)
        # Use YAML-driven group/conf mapping built at init
        response = []
        location_count = 0
        for index, value in enumerate(analyzed_data):
            try:
            
                location = f"{value['start']}_{value['end']}"
                entity_value = input_text[value['start']:value['end']]
                if anonymized_response:
                    anonymized_data = anonymized_response[index]
                    if anonymized_data["entity_type"] == value["entity_type"]:
                        location, location_count = self.update_anonymized_location(
                            anonymized_data["start"],
                            anonymized_data["end"],
                            location_count,
                        )
                _min, _grp = self._group_conf.get(value["entity_type"], (0.0, "unknown"))
                if _grp == "unknown":
                    continue
                response.append(
                    {
                        "entity_type": self._display_name.get(value["entity_type"], value["entity_type"]),
                        "location": location,
                        "confidence_score": value["score"],
                        "entity_value": entity_value,
                        "start_index": value['start'],
                        "end_index": value['end'],
                    }
                )
            except Exception:
                logger.exception(
                    "Failed to build entity response for %s", value
                )
        return response

    def _aggregate_entities_yaml(self, entities_response: list) -> Tuple[dict, dict, int]:
        """Aggregate counts and details using YAML entity ids and global group mapping."""
        entity_details: dict = {}
        for entry in entities_response:
            mapped_entity = entry.get("entity_type")
            detail = {
                "location": entry.get("location"),
                "confidence_score": entry.get("confidence_score"),
                "entity_value": entry.get("entity_value"),
                "start_index": entry.get("start_index"),
                "end_index": entry.get("end_index"),
            }
            entity_details.setdefault(mapped_entity, []).append(detail)
        return entity_details
    
    def entity_classifier_and_anonymizer(
        self, input_text: str, anonymize_snippets: bool = False
    ) -> (dict, str):
        """Main entry point returning aggregated entities, counts, and optional anonymized text.

        Args:
            input_text: Text to process.
            anonymize_snippets: Whether to produce anonymized snippets output.

        Returns:
            Tuple of (aggregated entities, total count, possibly anonymized text,
            detailed entity info).

        Failure Modes:
            Logs and returns empty aggregates with original text when exceptions arise.
        """
        entity_details = {}
        try:
            logger.debug("Presidio Entity Classifier and Anonymizer V2 Started.")

            analyzer_results = self.analyze_response(input_text)
            if anonymize_snippets:
                anonymized_response, anonymized_text = self.anonymize_response(
                    analyzer_results
                )
                input_text = anonymized_text.replace("<", "&lt;").replace(">", "&gt;")
                entities_response = self.get_analyzed_entities_response(
                    analyzer_results, anonymized_response, input_text
                )
            else:
                entities_response = self.get_analyzed_entities_response(
                    analyzer_results, None,input_text

                )

            entity_details = self._aggregate_entities_yaml(entities_response)

            return entity_details, input_text
        except Exception:
            import traceback
            logger.error(
                f"Presidio Entity Classifier and Anonymizer V2 Failed, Exception: {traceback.format_exc()}"
            )
            return entity_details, input_text