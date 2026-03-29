"""AUTOSAR spec data models - shared by registry and version modules."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ApiSpec:
    """Specification for a single API function."""
    name: str
    return_type: str
    params: list[str]
    mandatory: bool = True
    description: str = ""
    api_service_id: int = -1
    since_version: str = "4.0.3"


@dataclass
class DetErrorSpec:
    """DET error specification."""
    name: str
    value: int
    description: str = ""


@dataclass
class CallRelation:
    """Cross-module call relationship."""
    caller_module: str
    caller_api: str
    callee_module: str
    callee_api: str
    direction: str = "tx"
    description: str = ""


@dataclass
class ModuleSpec:
    """Complete specification for a BSW module."""
    name: str
    module_id: int
    description: str = ""
    apis: list[ApiSpec] = field(default_factory=list)
    required_includes: list[str] = field(default_factory=list)
    config_type: str = ""
    det_errors: list[DetErrorSpec] = field(default_factory=list)
    calls_to: list[str] = field(default_factory=list)
    called_by: list[str] = field(default_factory=list)
    has_main_function: bool = False
    main_function_names: list[str] = field(default_factory=list)
    init_dependencies: list[str] = field(default_factory=list)
    layer: str = ""


@dataclass
class VersionSpec:
    """Complete AUTOSAR version specification."""
    version: str
    modules: dict[str, ModuleSpec] = field(default_factory=dict)
    call_relations: list[CallRelation] = field(default_factory=list)
    init_order: list[str] = field(default_factory=list)
