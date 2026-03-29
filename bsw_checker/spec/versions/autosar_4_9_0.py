"""AUTOSAR 4.9.0 (Classic Platform R22-11) BSW Module Specifications.

Changes from 4.4.0:
- Enhanced security modules (SecOC, KeyM)
- Com_GetStatus added
- Enhanced Dem APIs
- J1939 support additions
- IdsM (Intrusion Detection) module added
"""

import copy
from .autosar_4_4_0 import get_spec as get_4_4_0_spec
from ..models import ApiSpec, DetErrorSpec, ModuleSpec, CallRelation, VersionSpec


def get_spec() -> VersionSpec:
    """Get AUTOSAR 4.9.0 spec by patching 4.4.0."""
    spec = copy.deepcopy(get_4_4_0_spec())
    spec.version = "4.9.0"

    # === Com enhancements ===
    if "Com" in spec.modules:
        com = spec.modules["Com"]
        com.apis.extend([
            ApiSpec(name="Com_GetStatus", return_type="Com_StatusType",
                    params=[], api_service_id=0x07, mandatory=False,
                    since_version="4.9.0",
                    description="Returns current status of COM module"),
            ApiSpec(name="Com_SendSignalGroup", return_type="uint8",
                    params=["Com_SignalGroupIdType"],
                    api_service_id=0x0D, mandatory=False, since_version="4.9.0"),
            ApiSpec(name="Com_ReceiveSignalGroup", return_type="uint8",
                    params=["Com_SignalGroupIdType"],
                    api_service_id=0x0E, mandatory=False, since_version="4.9.0"),
            ApiSpec(name="Com_SwitchIpduTxMode", return_type="void",
                    params=["PduIdType", "boolean"],
                    api_service_id=0x27, mandatory=False, since_version="4.9.0"),
        ])

    # === Det enhancements ===
    if "Det" in spec.modules:
        det = spec.modules["Det"]
        # Ensure Det_ReportRuntimeError is mandatory in 4.9.0
        for api in det.apis:
            if api.name == "Det_ReportRuntimeError":
                api.mandatory = True

    # === Dem enhancements ===
    if "Dem" in spec.modules:
        dem = spec.modules["Dem"]
        dem.apis.extend([
            ApiSpec(name="Dem_GetEventUdsStatus", return_type="Std_ReturnType",
                    params=["Dem_EventIdType", "Dem_UdsStatusByteType*"],
                    api_service_id=0x0A, mandatory=False, since_version="4.9.0"),
            ApiSpec(name="Dem_GetNumberOfEventMemoryEntries", return_type="Std_ReturnType",
                    params=["Dem_DTCOriginType", "uint8*"],
                    api_service_id=0xB1, mandatory=False, since_version="4.9.0"),
        ])

    # === Dcm enhancements ===
    if "Dcm" in spec.modules:
        dcm = spec.modules["Dcm"]
        dcm.apis.extend([
            ApiSpec(name="Dcm_GetSecurityLevel", return_type="Std_ReturnType",
                    params=["Dcm_SecLevelType*"],
                    api_service_id=0x0D, mandatory=False, since_version="4.9.0"),
            ApiSpec(name="Dcm_GetSesCtrlType", return_type="Std_ReturnType",
                    params=["Dcm_SesCtrlType*"],
                    api_service_id=0x06, mandatory=False, since_version="4.9.0"),
        ])

    # === Add SecOC module ===
    spec.modules["SecOC"] = ModuleSpec(
        name="SecOC",
        module_id=150,
        description="Secured Onboard Communication",
        layer="com",
        config_type="SecOC_ConfigType",
        has_main_function=True,
        main_function_names=["SecOC_MainFunctionRx", "SecOC_MainFunctionTx"],
        required_includes=["SecOC_Types.h", "ComStack_Types.h"],
        init_dependencies=["PduR"],
        calls_to=["PduR_SecOCTransmit"],
        called_by=["SecOC_RxIndication", "SecOC_TxConfirmation"],
        apis=[
            ApiSpec(name="SecOC_Init", return_type="void",
                    params=["const SecOC_ConfigType*"], api_service_id=0x01,
                    since_version="4.9.0"),
            ApiSpec(name="SecOC_DeInit", return_type="void",
                    params=[], api_service_id=0x05, since_version="4.9.0"),
            ApiSpec(name="SecOC_RxIndication", return_type="void",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x42, since_version="4.9.0"),
            ApiSpec(name="SecOC_TxConfirmation", return_type="void",
                    params=["PduIdType", "Std_ReturnType"],
                    api_service_id=0x40, since_version="4.9.0"),
            ApiSpec(name="SecOC_Transmit", return_type="Std_ReturnType",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x49, since_version="4.9.0"),
            ApiSpec(name="SecOC_MainFunctionRx", return_type="void",
                    params=[], api_service_id=0x06, since_version="4.9.0"),
            ApiSpec(name="SecOC_MainFunctionTx", return_type="void",
                    params=[], api_service_id=0x07, since_version="4.9.0"),
        ],
        det_errors=[
            DetErrorSpec(name="SECOC_E_UNINIT", value=0x01),
            DetErrorSpec(name="SECOC_E_PARAM", value=0x02),
            DetErrorSpec(name="SECOC_E_PARAM_POINTER", value=0x03),
        ],
    )

    # === Add IdsM module ===
    spec.modules["IdsM"] = ModuleSpec(
        name="IdsM",
        module_id=161,
        description="Intrusion Detection System Manager",
        layer="services",
        config_type="IdsM_ConfigType",
        has_main_function=True,
        main_function_names=["IdsM_MainFunction"],
        required_includes=["IdsM_Types.h"],
        init_dependencies=["Dem"],
        apis=[
            ApiSpec(name="IdsM_Init", return_type="void",
                    params=["const IdsM_ConfigType*"], api_service_id=0x01,
                    since_version="4.9.0"),
            ApiSpec(name="IdsM_MainFunction", return_type="void",
                    params=[], api_service_id=0x04, since_version="4.9.0"),
        ],
        det_errors=[
            DetErrorSpec(name="IDSM_E_UNINIT", value=0x01),
        ],
    )

    # === CanIf enhancements ===
    if "CanIf" in spec.modules:
        canif = spec.modules["CanIf"]
        canif.apis.append(
            ApiSpec(name="CanIf_GetTxConfirmationState", return_type="CanIf_NotifStatusType",
                    params=["uint8"],
                    api_service_id=0x19, mandatory=False, since_version="4.9.0")
        )

    # Update init order for 4.9.0
    spec.init_order.extend(["SecOC", "IdsM"])

    # Additional call relations
    spec.call_relations.extend([
        CallRelation("SecOC", "SecOC_Transmit", "PduR", "PduR_SecOCTransmit", "tx",
                      "SecOC transmits secured PDU via PduR"),
        CallRelation("PduR", "PduR_SecOCRxIndication", "SecOC", "SecOC_RxIndication", "rx",
                      "PduR forwards to SecOC for verification"),
    ])

    return spec
