from __future__ import annotations

from typing import Dict, List

from classifier.entity_classifier_2.core.config import CountryConfig, EntityConfig, LLMTemplate


class PromptProvider:
    """Formats detection and validation messages using country defaults
    with per-entity overrides when present.
    """

    def __init__(self, cfg: CountryConfig):
        self._cfg = cfg

    def _resolve_template(self, entity_id: str, kind: str) -> LLMTemplate:
        entity_llm = self._cfg.entities.get(entity_id).llm if entity_id in self._cfg.entities else None
        if entity_llm:
            tmpl = getattr(entity_llm, kind)
            if tmpl and (tmpl.system or tmpl.user_template):
                return tmpl
        defaults = self._cfg.llm
        return getattr(defaults, kind) if defaults else LLMTemplate()

    def get_detection_messages(self, *, text: str, entity_ids: List[str]) -> List[Dict[str, str]]:
        tmpl = (self._cfg.llm.detection if self._cfg.llm else LLMTemplate())
        # Build schema from output keys
        output_keys: List[str] = []
        for eid in entity_ids:
            ent = self._cfg.entities[eid]
            output_key = (ent.llm.output_key if ent.llm and ent.llm.output_key else eid.replace('-', '_').upper())
            output_keys.append(output_key)

        # Build JSON schema block { "KEY": [""] , ... } in the same order
        schema_lines: List[str] = ["{"]
        for i, key in enumerate(output_keys):
            comma = "," if i < len(output_keys) - 1 else ""
            schema_lines.append(f'  "{key}": [""]{comma}')
        schema_lines.append("}")
        schema_json = "\n".join(schema_lines)

        # Build entities_doc from YAML (description, context, examples, notes)
        entities_doc_lines: List[str] = []
        for eid in entity_ids:
            ent = self._cfg.entities[eid]
            out_key = (ent.llm.output_key if ent.llm and ent.llm.output_key else eid.replace('-', '_').upper())
            desc = (ent.llm.description or "").strip() if ent.llm else ""
            ctx = ent.context_indicators or []
            exs = (ent.llm.examples or []) if ent.llm else []
            notes = (ent.llm.notes or []) if ent.llm else []
            if desc:
                entities_doc_lines.append(f"- **{out_key}**: {desc}")
            else:
                entities_doc_lines.append(f"- **{out_key}**")
            if ctx:
                entities_doc_lines.append(f"  - Context indicators: {', '.join(ctx)}")
            if exs:
                entities_doc_lines.append(f"  - Examples: {', '.join(exs)}")
            if notes:
                entities_doc_lines.append(f"  - Notes: {' '.join(notes)}")
            # add an empty line after each entity block
            entities_doc_lines.append("")
        entities_doc_rendered = "\n".join(entities_doc_lines)

        # Render system with compose sections if present
        # Compose system content: prefer structured sections if compose is provided
        if getattr(tmpl, "compose", None):
            parts: List[str] = []
            mapping = {
                "role": tmpl.role or "",
                "instructions": tmpl.instructions or "",
                "entities_doc": (tmpl.entities_doc or "{entities_doc}").replace("{entities_doc}", entities_doc_rendered),
                "extraction_rules": tmpl.extraction_rules or "",
                "cot": tmpl.cot or "",
                "output_json_schema": (tmpl.output_json_schema or "{output_json_schema}").replace("{output_json_schema}", schema_json),
                "reflection": tmpl.reflection or "",
            }
            for key in tmpl.compose:
                val = mapping.get(key, "")
                if val:
                    parts.append(val)
            system_content = "\n".join(parts)
        else:
            system_content = (tmpl.system or "").replace("{entities_doc}", entities_doc_rendered).replace("{output_json_schema}", schema_json)
            if not system_content:
                system_content = f"## Entities\n{entities_doc_rendered}\n\n## Output JSON Schema\n{schema_json}"

        # Render user
        user = tmpl.user_template or "**Sentence:** {text}"
        user_rendered = user.format(text=text)

        return [
            {"role": "system", "content": system_content.strip()},
            {"role": "user", "content": user_rendered},
        ]

    def get_entity_detection_messages(self, *, text: str, entity_id: str) -> List[Dict[str, str]]:
        tmpl = self._resolve_template(entity_id, "detection")
        user = tmpl.user_template or "TEXT: {text}\nOUTPUT: {{\"%s\": []}}" % entity_id
        return [
            {"role": "system", "content": tmpl.system or ""},
            {"role": "user", "content": user.format(text=text)},
        ]

    def get_validation_messages(self, *, text: str, entities_for_validation: List[Dict[str, str]], entity_id: str | None = None) -> List[Dict[str, str]]:
        tmpl = self._resolve_template(entity_id, "validation") if entity_id else (self._cfg.llm.validation if self._cfg.llm else LLMTemplate())
        user = tmpl.user_template or "TEXT: {text}\nENTITIES: {entities_json}"
        return [
            {"role": "system", "content": tmpl.system or ""},
            {"role": "user", "content": user.format(text=text, entities_json=entities_for_validation)},
        ]


