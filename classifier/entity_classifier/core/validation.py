from __future__ import annotations

import importlib
from typing import Callable, Optional
from classifier.log import get_logger


logger = get_logger(__name__)


class ValidationRules:
    """Default, generic validators.

    Country analyzers should define their own functions; these are fallbacks.
    """

    @staticmethod
    def always_true(value: str, text: str, country: str, rules: dict) -> bool:
        return True


class ValidationProvider:
    """Resolve and invoke validation functions specified by name or dotted path.

    Resolution order:
    1) Dotted path: 'pkg.mod.func' → import and call
    2) Country analyzer module: 'pebblo.entity_classifier_2.analyzers.<cc>_analyzer'
       Look up <fn> in that module
    3) Fallback to ValidationRules.<fn> if present, else ValidationRules.always_true
    """

    def _import_object(self, dotted_path: str) -> Callable[..., bool]:
        module_path, _, attr = dotted_path.rpartition(".")
        if not module_path or not attr:
            raise ImportError(f"Invalid dotted path: {dotted_path}")
        module = importlib.import_module(module_path)
        func = getattr(module, attr)
        if not callable(func):
            raise AttributeError(f"Object {dotted_path} is not callable")
        return func  # type: ignore[return-value]

    def _resolve_in_country(self, country: str, fn: str) -> Optional[Callable[..., bool]]:
        cc = (country or "").strip().lower()
        if not cc:
            return None
        # Prefer '<cc>_analyzer' naming
        module_names = [
            f"classifier.entity_classifier_2.analyzers.{cc}_analyzer",
            f"pebclassifierblo.entity_classifier_2.analyzers.{cc}",
        ]
        for mod_name in module_names:
            try:
                module = importlib.import_module(mod_name)
                # 1) module-level function
                func = getattr(module, fn, None)
                if callable(func):
                    return func  # type: ignore[return-value]
                # 2) search analyzer classes in module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name, None)
                    if isinstance(attr, type) and hasattr(attr, fn):
                        cand = getattr(attr, fn, None)
                        if callable(cand):
                            return cand  # type: ignore[return-value]
            except Exception as exc:
                logger.debug(
                    "error importing module '%s' for country '%s': %s",
                    mod_name,
                    country,
                    exc,
                )
                continue
        return None

    def validate(
        self,
        fn: str,
        value: str,
        text: str,
        country: str,
        rules: Optional[dict] = None,
    ) -> bool:
        """Invoke a validator by name or path.

        Supports flexible function arity for validators:
        (value), (value, text), (value, text, country), or (value, text, country, rules).
        """
        rules = rules or {}

        def _call_flex(func):
            try:
                return bool(func(value, text, country, rules))
            except TypeError:
                try:
                    return bool(func(value, text, country))
                except TypeError:
                    try:
                        return bool(func(value, text))
                    except TypeError:
                        return bool(func(value))

        try:
            # dotted path
            if "." in (fn or ""):
                func = self._import_object(fn)
                return _call_flex(func)

            # country analyzer lookup
            func = self._resolve_in_country(country, fn)
            if func is not None:
                return _call_flex(func)

            # fallback to builtin rules
            fallback = getattr(ValidationRules, fn, ValidationRules.always_true)
            return _call_flex(fallback)
        except Exception as exc:
            logger.exception(
                "Validation invocation failed for fn='%s' country='%s'", fn, country,
            )
            return False


