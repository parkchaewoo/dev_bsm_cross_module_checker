"""AUTOSAR BSW Module Specification Registry.

Manages module specs across multiple AUTOSAR versions.
Supports: 4.0.3, 4.4.0, 4.9.0, 20.0.0 (Adaptive/Classic R20-11)
"""

from typing import Optional

from .models import (
    ApiSpec, CallRelation, DetErrorSpec, ModuleSpec, VersionSpec,
)

# Re-export for backwards compatibility
__all__ = [
    'ApiSpec', 'CallRelation', 'DetErrorSpec', 'ModuleSpec', 'VersionSpec',
    'ModuleRegistry', 'SUPPORTED_VERSIONS',
]

SUPPORTED_VERSIONS = ["4.0.3", "4.4.0", "4.9.0", "20.0.0"]


class ModuleRegistry:
    """Registry managing AUTOSAR module specs across versions."""

    def __init__(self):
        self._versions: dict[str, VersionSpec] = {}
        self._load_all_versions()

    def _load_all_versions(self):
        """Load all supported AUTOSAR version specs."""
        from .versions import autosar_4_0_3, autosar_4_4_0, autosar_4_9_0, autosar_20_0_0
        self._versions["4.0.3"] = autosar_4_0_3.get_spec()
        self._versions["4.4.0"] = autosar_4_4_0.get_spec()
        self._versions["4.9.0"] = autosar_4_9_0.get_spec()
        self._versions["20.0.0"] = autosar_20_0_0.get_spec()

    def get_version_spec(self, version: str) -> Optional[VersionSpec]:
        return self._versions.get(version)

    def get_module_spec(self, version: str, module_name: str) -> Optional[ModuleSpec]:
        ver = self._versions.get(version)
        if ver:
            return ver.modules.get(module_name)
        return None

    def get_supported_modules(self, version: str) -> list[str]:
        ver = self._versions.get(version)
        if ver:
            return sorted(ver.modules.keys())
        return []

    def get_call_relations(self, version: str) -> list[CallRelation]:
        ver = self._versions.get(version)
        if ver:
            return ver.call_relations
        return []

    def get_init_order(self, version: str) -> list[str]:
        ver = self._versions.get(version)
        if ver:
            return ver.init_order
        return []

    @property
    def supported_versions(self) -> list[str]:
        return SUPPORTED_VERSIONS
