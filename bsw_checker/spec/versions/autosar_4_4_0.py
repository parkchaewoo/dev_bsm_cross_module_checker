"""AUTOSAR 4.4.0 (Classic Platform R19-11) BSW Module Specifications.

Changes from 4.0.3:
- Com_TxConfirmation now has 2 params (PduIdType, Std_ReturnType)
- CanIf_RxIndication changed to (Can_HwType*, PduInfoType*) with CanId
- Added Det_ReportRuntimeError
- Added Com_SendDynSignal / Com_ReceiveDynSignal
- CanIf_ControllerModeIndication renamed to CanIf_ControllerModeIndication
- PduR enhanced with TP APIs
"""

import copy
from .autosar_4_0_3 import get_spec as get_4_0_3_spec
from ..models import ApiSpec, CallRelation, DetErrorSpec, ModuleSpec, VersionSpec


def get_spec() -> VersionSpec:
    """Get AUTOSAR 4.4.0 spec by patching 4.0.3."""
    spec = copy.deepcopy(get_4_0_3_spec())
    spec.version = "4.4.0"

    # === Com changes ===
    if "Com" in spec.modules:
        com = spec.modules["Com"]
        # TxConfirmation now includes result parameter
        for api in com.apis:
            if api.name == "Com_TxConfirmation":
                api.params = ["PduIdType", "Std_ReturnType"]
                api.description = "Tx confirmation callback (with result in 4.4.0)"
        # Add new APIs
        com.apis.extend([
            ApiSpec(name="Com_SendDynSignal", return_type="uint8",
                    params=["Com_SignalIdType", "const void*", "uint16"],
                    api_service_id=0x21, mandatory=False, since_version="4.4.0",
                    description="Send dynamic length signal"),
            ApiSpec(name="Com_ReceiveDynSignal", return_type="uint8",
                    params=["Com_SignalIdType", "void*", "uint16*"],
                    api_service_id=0x22, mandatory=False, since_version="4.4.0",
                    description="Receive dynamic length signal"),
        ])

    # === Det changes ===
    if "Det" in spec.modules:
        det = spec.modules["Det"]
        det.apis.append(
            ApiSpec(name="Det_ReportRuntimeError", return_type="Std_ReturnType",
                    params=["uint16", "uint8", "uint8", "uint8"],
                    api_service_id=0x04, since_version="4.4.0",
                    description="Report a runtime error (new in 4.4.0)")
        )
        det.apis.append(
            ApiSpec(name="Det_ReportTransientFault", return_type="Std_ReturnType",
                    params=["uint16", "uint8", "uint8", "uint8"],
                    api_service_id=0x05, mandatory=False, since_version="4.4.0",
                    description="Report a transient fault (new in 4.4.0)")
        )

    # === PduR changes - add TP APIs ===
    if "PduR" in spec.modules:
        pdur = spec.modules["PduR"]
        pdur.apis.extend([
            ApiSpec(name="PduR_CanTpStartOfReception", return_type="BufReq_ReturnType",
                    params=["PduIdType", "const PduInfoType*", "PduLengthType", "PduLengthType*"],
                    api_service_id=0x46, mandatory=False, since_version="4.4.0"),
            ApiSpec(name="PduR_CanTpCopyRxData", return_type="BufReq_ReturnType",
                    params=["PduIdType", "const PduInfoType*", "PduLengthType*"],
                    api_service_id=0x44, mandatory=False, since_version="4.4.0"),
            ApiSpec(name="PduR_CanTpRxIndication", return_type="void",
                    params=["PduIdType", "Std_ReturnType"],
                    api_service_id=0x45, mandatory=False, since_version="4.4.0"),
            ApiSpec(name="PduR_CanTpCopyTxData", return_type="BufReq_ReturnType",
                    params=["PduIdType", "const PduInfoType*", "RetryInfoType*", "PduLengthType*"],
                    api_service_id=0x43, mandatory=False, since_version="4.4.0"),
            ApiSpec(name="PduR_CanTpTxConfirmation", return_type="void",
                    params=["PduIdType", "Std_ReturnType"],
                    api_service_id=0x48, mandatory=False, since_version="4.4.0"),
        ])

    # === CanIf changes ===
    if "CanIf" in spec.modules:
        canif = spec.modules["CanIf"]
        # TxConfirmation now includes result
        for api in canif.apis:
            if api.name == "CanIf_TxConfirmation":
                api.params = ["PduIdType", "Std_ReturnType"]
        # Add CanIf_SetDynamicTxId
        canif.apis.append(
            ApiSpec(name="CanIf_SetDynamicTxId", return_type="void",
                    params=["PduIdType", "Can_IdType"],
                    api_service_id=0x0C, mandatory=False, since_version="4.4.0")
        )

    # === Dem changes ===
    if "Dem" in spec.modules:
        dem = spec.modules["Dem"]
        dem.apis.append(
            ApiSpec(name="Dem_GetDTCOfEvent", return_type="Std_ReturnType",
                    params=["Dem_EventIdType", "Dem_DTCFormatType", "uint32*"],
                    api_service_id=0x0D, mandatory=False, since_version="4.4.0")
        )

    # === Add CanTp module ===
    spec.modules["CanTp"] = ModuleSpec(
        name="CanTp",
        module_id=35,
        description="CAN Transport Protocol",
        layer="com",
        config_type="CanTp_ConfigType",
        has_main_function=True,
        main_function_names=["CanTp_MainFunction"],
        required_includes=["CanTp_Types.h", "ComStack_Types.h"],
        init_dependencies=["CanIf", "PduR"],
        calls_to=["CanIf_Transmit", "PduR_CanTpStartOfReception",
                   "PduR_CanTpCopyRxData", "PduR_CanTpRxIndication",
                   "PduR_CanTpCopyTxData", "PduR_CanTpTxConfirmation"],
        called_by=["CanTp_Transmit", "CanTp_RxIndication"],
        apis=[
            ApiSpec(name="CanTp_Init", return_type="void",
                    params=["const CanTp_ConfigType*"], api_service_id=0x01),
            ApiSpec(name="CanTp_Transmit", return_type="Std_ReturnType",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x49),
            ApiSpec(name="CanTp_RxIndication", return_type="void",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x42),
            ApiSpec(name="CanTp_TxConfirmation", return_type="void",
                    params=["PduIdType", "Std_ReturnType"],
                    api_service_id=0x40),
            ApiSpec(name="CanTp_MainFunction", return_type="void",
                    params=[], api_service_id=0x06),
        ],
        det_errors=[
            DetErrorSpec(name="CANTP_E_UNINIT", value=0x20),
            DetErrorSpec(name="CANTP_E_PARAM_ID", value=0x02),
        ],
    )

    # Update call relations for 4.4.0
    spec.call_relations.extend([
        CallRelation("CanTp", "CanTp_Transmit", "CanIf", "CanIf_Transmit", "tx",
                      "CanTp transmits SF/FF/CF via CanIf"),
        CallRelation("CanIf", "CanIf_RxIndication", "CanTp", "CanTp_RxIndication", "rx",
                      "CanIf forwards TP frames to CanTp"),
    ])

    return spec
