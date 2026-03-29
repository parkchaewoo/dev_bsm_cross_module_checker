"""AUTOSAR 4.0.3 (Classic Platform) BSW Module Specifications."""

from ..models import (
    ApiSpec, CallRelation, DetErrorSpec, ModuleSpec, VersionSpec,
)


def _com_spec() -> ModuleSpec:
    return ModuleSpec(
        name="Com",
        module_id=50,
        description="AUTOSAR COM Module - Signal-based communication",
        layer="com",
        config_type="Com_ConfigType",
        has_main_function=True,
        main_function_names=["Com_MainFunctionRx", "Com_MainFunctionTx"],
        required_includes=["Com_Types.h", "ComStack_Types.h"],
        init_dependencies=["PduR"],
        calls_to=["PduR_ComTransmit"],
        called_by=["Com_RxIndication", "Com_TxConfirmation", "Com_TriggerTransmit"],
        apis=[
            ApiSpec(name="Com_Init", return_type="void",
                    params=["const Com_ConfigType*"], api_service_id=0x01,
                    description="Initializes the COM module"),
            ApiSpec(name="Com_DeInit", return_type="void",
                    params=[], api_service_id=0x02,
                    description="De-initializes the COM module"),
            ApiSpec(name="Com_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x09),
            ApiSpec(name="Com_SendSignal", return_type="uint8",
                    params=["Com_SignalIdType", "const void*"],
                    api_service_id=0x0A,
                    description="Sends a signal value"),
            ApiSpec(name="Com_ReceiveSignal", return_type="uint8",
                    params=["Com_SignalIdType", "void*"],
                    api_service_id=0x0B,
                    description="Receives a signal value"),
            ApiSpec(name="Com_MainFunctionRx", return_type="void",
                    params=[], api_service_id=0x18,
                    description="Rx main processing function"),
            ApiSpec(name="Com_MainFunctionTx", return_type="void",
                    params=[], api_service_id=0x19,
                    description="Tx main processing function"),
            ApiSpec(name="Com_RxIndication", return_type="void",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x42,
                    description="Rx indication callback from PduR"),
            ApiSpec(name="Com_TxConfirmation", return_type="void",
                    params=["PduIdType"],
                    api_service_id=0x40,
                    description="Tx confirmation callback from PduR"),
            ApiSpec(name="Com_TriggerTransmit", return_type="Std_ReturnType",
                    params=["PduIdType", "PduInfoType*"],
                    api_service_id=0x41, mandatory=False),
            ApiSpec(name="Com_IpduGroupStart", return_type="void",
                    params=["Com_IpduGroupIdType", "boolean"],
                    api_service_id=0x03, mandatory=False),
            ApiSpec(name="Com_IpduGroupStop", return_type="void",
                    params=["Com_IpduGroupIdType"],
                    api_service_id=0x04, mandatory=False),
        ],
        det_errors=[
            DetErrorSpec(name="COM_E_PARAM", value=0x01, description="API called with wrong parameter"),
            DetErrorSpec(name="COM_E_UNINIT", value=0x02, description="API called before init"),
            DetErrorSpec(name="COM_E_PARAM_POINTER", value=0x03, description="Null pointer parameter"),
        ],
    )


def _pdur_spec() -> ModuleSpec:
    return ModuleSpec(
        name="PduR",
        module_id=51,
        description="PDU Router - Routes PDUs between BSW modules",
        layer="com",
        config_type="PduR_ConfigType",
        has_main_function=False,
        required_includes=["PduR_Types.h", "ComStack_Types.h"],
        init_dependencies=["CanIf", "LinIf"],
        calls_to=["CanIf_Transmit", "LinIf_Transmit", "Com_RxIndication",
                   "Com_TxConfirmation", "Dcm_RxIndication", "Dcm_TxConfirmation"],
        called_by=["PduR_ComTransmit", "PduR_DcmTransmit",
                    "PduR_CanIfRxIndication", "PduR_CanIfTxConfirmation",
                    "PduR_LinIfRxIndication", "PduR_LinIfTxConfirmation"],
        apis=[
            ApiSpec(name="PduR_Init", return_type="void",
                    params=["const PduR_ConfigType*"], api_service_id=0x01),
            ApiSpec(name="PduR_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x02),
            ApiSpec(name="PduR_ComTransmit", return_type="Std_ReturnType",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x49,
                    description="Transmit request from COM"),
            ApiSpec(name="PduR_DcmTransmit", return_type="Std_ReturnType",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x49, mandatory=False),
            ApiSpec(name="PduR_CanIfRxIndication", return_type="void",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x42,
                    description="Rx indication from CanIf"),
            ApiSpec(name="PduR_CanIfTxConfirmation", return_type="void",
                    params=["PduIdType"],
                    api_service_id=0x40),
            ApiSpec(name="PduR_LinIfRxIndication", return_type="void",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x42, mandatory=False),
        ],
        det_errors=[
            DetErrorSpec(name="PDUR_E_INIT_FAILED", value=0x00),
            DetErrorSpec(name="PDUR_E_UNINIT", value=0x01),
            DetErrorSpec(name="PDUR_E_PDU_ID_INVALID", value=0x02),
            DetErrorSpec(name="PDUR_E_TP_TX_REQ_REJECTED", value=0x03),
        ],
    )


def _canif_spec() -> ModuleSpec:
    return ModuleSpec(
        name="CanIf",
        module_id=60,
        description="CAN Interface - Abstract CAN driver access",
        layer="com",
        config_type="CanIf_ConfigType",
        has_main_function=False,
        required_includes=["CanIf_Types.h", "ComStack_Types.h", "Can_GeneralTypes.h"],
        init_dependencies=["Can"],
        calls_to=["Can_Write", "PduR_CanIfRxIndication", "PduR_CanIfTxConfirmation",
                   "CanSM_ControllerBusOff", "CanSM_ControllerModeIndication"],
        called_by=["CanIf_Transmit", "CanIf_RxIndication", "CanIf_TxConfirmation",
                    "CanIf_ControllerBusOff", "CanIf_ControllerModeIndication"],
        apis=[
            ApiSpec(name="CanIf_Init", return_type="void",
                    params=["const CanIf_ConfigType*"], api_service_id=0x01),
            ApiSpec(name="CanIf_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x0B),
            ApiSpec(name="CanIf_Transmit", return_type="Std_ReturnType",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x05,
                    description="Transmit a CAN L-PDU"),
            ApiSpec(name="CanIf_RxIndication", return_type="void",
                    params=["const Can_HwType*", "const PduInfoType*"],
                    api_service_id=0x14,
                    description="Rx indication from CAN driver"),
            ApiSpec(name="CanIf_TxConfirmation", return_type="void",
                    params=["PduIdType"],
                    api_service_id=0x13),
            ApiSpec(name="CanIf_ControllerBusOff", return_type="void",
                    params=["uint8"], api_service_id=0x16),
            ApiSpec(name="CanIf_SetControllerMode", return_type="Std_ReturnType",
                    params=["uint8", "CanIf_ControllerModeType"],
                    api_service_id=0x03),
            ApiSpec(name="CanIf_GetControllerMode", return_type="Std_ReturnType",
                    params=["uint8", "CanIf_ControllerModeType*"],
                    api_service_id=0x04),
            ApiSpec(name="CanIf_SetPduMode", return_type="Std_ReturnType",
                    params=["uint8", "CanIf_PduModeType"],
                    api_service_id=0x09),
        ],
        det_errors=[
            DetErrorSpec(name="CANIF_E_PARAM_CANID", value=0x10),
            DetErrorSpec(name="CANIF_E_PARAM_DLC", value=0x11),
            DetErrorSpec(name="CANIF_E_PARAM_HRH", value=0x12),
            DetErrorSpec(name="CANIF_E_PARAM_LPDU", value=0x13),
            DetErrorSpec(name="CANIF_E_PARAM_CONTROLLER", value=0x14),
            DetErrorSpec(name="CANIF_E_UNINIT", value=0x30),
        ],
    )


def _can_spec() -> ModuleSpec:
    return ModuleSpec(
        name="Can",
        module_id=80,
        description="CAN Driver - Hardware abstraction for CAN controller",
        layer="mcal",
        config_type="Can_ConfigType",
        has_main_function=True,
        main_function_names=["Can_MainFunction_Write", "Can_MainFunction_Read",
                             "Can_MainFunction_BusOff", "Can_MainFunction_Mode"],
        required_includes=["Can_GeneralTypes.h", "ComStack_Types.h"],
        init_dependencies=[],
        calls_to=["CanIf_RxIndication", "CanIf_TxConfirmation",
                   "CanIf_ControllerBusOff", "CanIf_ControllerModeIndication"],
        called_by=["Can_Init", "Can_Write", "Can_SetControllerMode"],
        apis=[
            ApiSpec(name="Can_Init", return_type="void",
                    params=["const Can_ConfigType*"], api_service_id=0x00),
            ApiSpec(name="Can_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x07),
            ApiSpec(name="Can_Write", return_type="Can_ReturnType",
                    params=["Can_HwHandleType", "const Can_PduType*"],
                    api_service_id=0x06,
                    description="Initiate CAN frame transmission"),
            ApiSpec(name="Can_SetControllerMode", return_type="Can_ReturnType",
                    params=["uint8", "Can_StateTransitionType"],
                    api_service_id=0x03),
            ApiSpec(name="Can_MainFunction_Write", return_type="void",
                    params=[], api_service_id=0x01),
            ApiSpec(name="Can_MainFunction_Read", return_type="void",
                    params=[], api_service_id=0x08),
            ApiSpec(name="Can_MainFunction_BusOff", return_type="void",
                    params=[], api_service_id=0x09),
            ApiSpec(name="Can_MainFunction_Mode", return_type="void",
                    params=[], api_service_id=0x0C),
        ],
        det_errors=[
            DetErrorSpec(name="CAN_E_PARAM_POINTER", value=0x01),
            DetErrorSpec(name="CAN_E_PARAM_HANDLE", value=0x02),
            DetErrorSpec(name="CAN_E_PARAM_DLC", value=0x03),
            DetErrorSpec(name="CAN_E_PARAM_CONTROLLER", value=0x04),
            DetErrorSpec(name="CAN_E_UNINIT", value=0x05),
            DetErrorSpec(name="CAN_E_TRANSITION", value=0x06),
        ],
    )


def _ecum_spec() -> ModuleSpec:
    return ModuleSpec(
        name="EcuM",
        module_id=10,
        description="ECU State Manager - Manages ECU states and initialization",
        layer="services",
        config_type="EcuM_ConfigType",
        has_main_function=True,
        main_function_names=["EcuM_MainFunction"],
        required_includes=["EcuM_Types.h"],
        init_dependencies=[],
        calls_to=["BswM_Init", "SchM_Init", "Os_Init",
                   "Det_Init", "Dem_PreInit", "Dem_Init",
                   "Can_Init", "CanIf_Init", "PduR_Init", "Com_Init",
                   "NvM_Init", "Fee_Init", "Fls_Init",
                   "ComM_Init", "CanSM_Init", "Dcm_Init"],
        called_by=[],
        apis=[
            ApiSpec(name="EcuM_Init", return_type="void",
                    params=[], api_service_id=0x01,
                    description="Initializes the ECU State Manager"),
            ApiSpec(name="EcuM_StartupTwo", return_type="void",
                    params=[], api_service_id=0x18),
            ApiSpec(name="EcuM_Shutdown", return_type="void",
                    params=[], api_service_id=0x02),
            ApiSpec(name="EcuM_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x00),
            ApiSpec(name="EcuM_GetState", return_type="Std_ReturnType",
                    params=["EcuM_StateType*"], api_service_id=0x07),
            ApiSpec(name="EcuM_RequestRUN", return_type="Std_ReturnType",
                    params=["EcuM_UserType"], api_service_id=0x03),
            ApiSpec(name="EcuM_ReleaseRUN", return_type="Std_ReturnType",
                    params=["EcuM_UserType"], api_service_id=0x04),
            ApiSpec(name="EcuM_MainFunction", return_type="void",
                    params=[], api_service_id=0x18),
            ApiSpec(name="EcuM_SetWakeupEvent", return_type="void",
                    params=["EcuM_WakeupSourceType"], api_service_id=0x0C),
        ],
        det_errors=[
            DetErrorSpec(name="ECUM_E_UNINIT", value=0x10),
            DetErrorSpec(name="ECUM_E_SERVICE_DISABLED", value=0x11),
            DetErrorSpec(name="ECUM_E_NULL_POINTER", value=0x12),
            DetErrorSpec(name="ECUM_E_INVALID_PAR", value=0x13),
        ],
    )


def _bswm_spec() -> ModuleSpec:
    return ModuleSpec(
        name="BswM",
        module_id=42,
        description="BSW Mode Manager - Manages BSW module modes",
        layer="services",
        config_type="BswM_ConfigType",
        has_main_function=True,
        main_function_names=["BswM_MainFunction"],
        required_includes=["BswM_Types.h"],
        init_dependencies=["EcuM"],
        apis=[
            ApiSpec(name="BswM_Init", return_type="void",
                    params=["const BswM_ConfigType*"], api_service_id=0x00),
            ApiSpec(name="BswM_DeInit", return_type="void",
                    params=[], api_service_id=0x04),
            ApiSpec(name="BswM_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x01),
            ApiSpec(name="BswM_MainFunction", return_type="void",
                    params=[], api_service_id=0x05),
            ApiSpec(name="BswM_RequestMode", return_type="void",
                    params=["BswM_UserType", "BswM_ModeType"],
                    api_service_id=0x02, mandatory=False),
        ],
        det_errors=[
            DetErrorSpec(name="BSWM_E_NULL_POINTER", value=0x04),
            DetErrorSpec(name="BSWM_E_UNINIT", value=0x01),
            DetErrorSpec(name="BSWM_E_PARAM_CONFIG", value=0x05),
        ],
    )


def _det_spec() -> ModuleSpec:
    return ModuleSpec(
        name="Det",
        module_id=15,
        description="Default Error Tracer - Development error detection",
        layer="services",
        config_type="",
        has_main_function=False,
        required_includes=[],
        init_dependencies=[],
        apis=[
            ApiSpec(name="Det_Init", return_type="void",
                    params=[], api_service_id=0x00),
            ApiSpec(name="Det_ReportError", return_type="Std_ReturnType",
                    params=["uint16", "uint8", "uint8", "uint8"],
                    api_service_id=0x01,
                    description="Report a development error"),
            ApiSpec(name="Det_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x03),
            ApiSpec(name="Det_Start", return_type="void",
                    params=[], api_service_id=0x02, mandatory=False),
        ],
        det_errors=[],
    )


def _dem_spec() -> ModuleSpec:
    return ModuleSpec(
        name="Dem",
        module_id=54,
        description="Diagnostic Event Manager",
        layer="diag",
        config_type="Dem_ConfigType",
        has_main_function=True,
        main_function_names=["Dem_MainFunction"],
        required_includes=["Dem_Types.h"],
        init_dependencies=["NvM"],
        apis=[
            ApiSpec(name="Dem_PreInit", return_type="void",
                    params=["const Dem_ConfigType*"], api_service_id=0x01),
            ApiSpec(name="Dem_Init", return_type="void",
                    params=[], api_service_id=0x02),
            ApiSpec(name="Dem_Shutdown", return_type="void",
                    params=[], api_service_id=0x03),
            ApiSpec(name="Dem_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x00),
            ApiSpec(name="Dem_SetEventStatus", return_type="Std_ReturnType",
                    params=["Dem_EventIdType", "Dem_EventStatusType"],
                    api_service_id=0x04),
            ApiSpec(name="Dem_ReportErrorStatus", return_type="void",
                    params=["Dem_EventIdType", "Dem_EventStatusType"],
                    api_service_id=0x0F),
            ApiSpec(name="Dem_MainFunction", return_type="void",
                    params=[], api_service_id=0x55),
        ],
        det_errors=[
            DetErrorSpec(name="DEM_E_PARAM_CONFIG", value=0x10),
            DetErrorSpec(name="DEM_E_PARAM_POINTER", value=0x11),
            DetErrorSpec(name="DEM_E_PARAM_DATA", value=0x12),
            DetErrorSpec(name="DEM_E_UNINIT", value=0x20),
        ],
    )


def _schm_spec() -> ModuleSpec:
    return ModuleSpec(
        name="SchM",
        module_id=130,
        description="Schedule Manager - BSW Scheduling",
        layer="services",
        config_type="",
        has_main_function=False,
        required_includes=[],
        init_dependencies=["Os"],
        apis=[
            ApiSpec(name="SchM_Init", return_type="void",
                    params=[], api_service_id=0x00),
            ApiSpec(name="SchM_DeInit", return_type="void",
                    params=[], api_service_id=0x01),
            ApiSpec(name="SchM_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x02),
        ],
        det_errors=[],
    )


def _os_spec() -> ModuleSpec:
    return ModuleSpec(
        name="Os",
        module_id=1,
        description="AUTOSAR OS",
        layer="services",
        config_type="",
        has_main_function=False,
        required_includes=[],
        init_dependencies=[],
        apis=[
            ApiSpec(name="Os_Init", return_type="void",
                    params=[], api_service_id=0x00, mandatory=False),
            ApiSpec(name="Os_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x01),
        ],
        det_errors=[],
    )


def _nvm_spec() -> ModuleSpec:
    return ModuleSpec(
        name="NvM",
        module_id=20,
        description="NVRAM Manager",
        layer="mem",
        config_type="NvM_ConfigType",
        has_main_function=True,
        main_function_names=["NvM_MainFunction"],
        required_includes=["NvM_Types.h"],
        init_dependencies=["MemIf", "Fee", "Fls"],
        calls_to=["MemIf_Read", "MemIf_Write", "MemIf_EraseImmediateBlock"],
        called_by=[],
        apis=[
            ApiSpec(name="NvM_Init", return_type="void",
                    params=[], api_service_id=0x00),
            ApiSpec(name="NvM_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x0F),
            ApiSpec(name="NvM_ReadBlock", return_type="Std_ReturnType",
                    params=["NvM_BlockIdType", "void*"],
                    api_service_id=0x06),
            ApiSpec(name="NvM_WriteBlock", return_type="Std_ReturnType",
                    params=["NvM_BlockIdType", "const void*"],
                    api_service_id=0x07),
            ApiSpec(name="NvM_ReadAll", return_type="void",
                    params=[], api_service_id=0x0C),
            ApiSpec(name="NvM_WriteAll", return_type="void",
                    params=[], api_service_id=0x0D),
            ApiSpec(name="NvM_MainFunction", return_type="void",
                    params=[], api_service_id=0x0E),
        ],
        det_errors=[
            DetErrorSpec(name="NVM_E_PARAM_BLOCK_ID", value=0x0A),
            DetErrorSpec(name="NVM_E_PARAM_BLOCK_TYPE", value=0x0B),
            DetErrorSpec(name="NVM_E_NOT_INITIALIZED", value=0x14),
        ],
    )


def _fee_spec() -> ModuleSpec:
    return ModuleSpec(
        name="Fee",
        module_id=21,
        description="Flash EEPROM Emulation",
        layer="mem",
        config_type="Fee_ConfigType",
        has_main_function=True,
        main_function_names=["Fee_MainFunction"],
        required_includes=[],
        init_dependencies=["Fls"],
        calls_to=["Fls_Read", "Fls_Write", "Fls_Erase"],
        apis=[
            ApiSpec(name="Fee_Init", return_type="void",
                    params=[], api_service_id=0x00),
            ApiSpec(name="Fee_Read", return_type="Std_ReturnType",
                    params=["uint16", "uint16", "uint8*", "uint16"],
                    api_service_id=0x02),
            ApiSpec(name="Fee_Write", return_type="Std_ReturnType",
                    params=["uint16", "uint8*"],
                    api_service_id=0x03),
            ApiSpec(name="Fee_MainFunction", return_type="void",
                    params=[], api_service_id=0x12),
        ],
        det_errors=[
            DetErrorSpec(name="FEE_E_UNINIT", value=0x01),
            DetErrorSpec(name="FEE_E_INVALID_BLOCK_NO", value=0x02),
        ],
    )


def _fls_spec() -> ModuleSpec:
    return ModuleSpec(
        name="Fls",
        module_id=92,
        description="Flash Driver",
        layer="mcal",
        config_type="Fls_ConfigType",
        has_main_function=True,
        main_function_names=["Fls_MainFunction"],
        required_includes=[],
        init_dependencies=[],
        apis=[
            ApiSpec(name="Fls_Init", return_type="void",
                    params=["const Fls_ConfigType*"], api_service_id=0x00),
            ApiSpec(name="Fls_Erase", return_type="Std_ReturnType",
                    params=["Fls_AddressType", "Fls_LengthType"],
                    api_service_id=0x01),
            ApiSpec(name="Fls_Write", return_type="Std_ReturnType",
                    params=["Fls_AddressType", "const uint8*", "Fls_LengthType"],
                    api_service_id=0x02),
            ApiSpec(name="Fls_Read", return_type="Std_ReturnType",
                    params=["Fls_AddressType", "uint8*", "Fls_LengthType"],
                    api_service_id=0x07),
            ApiSpec(name="Fls_MainFunction", return_type="void",
                    params=[], api_service_id=0x06),
        ],
        det_errors=[
            DetErrorSpec(name="FLS_E_PARAM_CONFIG", value=0x01),
            DetErrorSpec(name="FLS_E_UNINIT", value=0x11),
        ],
    )


def _ea_spec() -> ModuleSpec:
    return ModuleSpec(
        name="Ea",
        module_id=40,
        description="EEPROM Abstraction",
        layer="mem",
        config_type="Ea_ConfigType",
        has_main_function=True,
        main_function_names=["Ea_MainFunction"],
        required_includes=[],
        init_dependencies=["Eep"],
        apis=[
            ApiSpec(name="Ea_Init", return_type="void",
                    params=[], api_service_id=0x00),
            ApiSpec(name="Ea_Read", return_type="Std_ReturnType",
                    params=["uint16", "uint16", "uint8*", "uint16"],
                    api_service_id=0x02),
            ApiSpec(name="Ea_Write", return_type="Std_ReturnType",
                    params=["uint16", "uint8*"],
                    api_service_id=0x03),
            ApiSpec(name="Ea_MainFunction", return_type="void",
                    params=[], api_service_id=0x12),
        ],
        det_errors=[
            DetErrorSpec(name="EA_E_UNINIT", value=0x01),
        ],
    )


def _dcm_spec() -> ModuleSpec:
    return ModuleSpec(
        name="Dcm",
        module_id=53,
        description="Diagnostic Communication Manager",
        layer="diag",
        config_type="Dcm_ConfigType",
        has_main_function=True,
        main_function_names=["Dcm_MainFunction"],
        required_includes=["Dcm_Types.h", "ComStack_Types.h"],
        init_dependencies=["PduR", "Dem"],
        calls_to=["PduR_DcmTransmit", "Dem_SetEventStatus"],
        called_by=["Dcm_RxIndication", "Dcm_TxConfirmation"],
        apis=[
            ApiSpec(name="Dcm_Init", return_type="void",
                    params=["const Dcm_ConfigType*"], api_service_id=0x01),
            ApiSpec(name="Dcm_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x24),
            ApiSpec(name="Dcm_MainFunction", return_type="void",
                    params=[], api_service_id=0x25),
            ApiSpec(name="Dcm_RxIndication", return_type="void",
                    params=["PduIdType", "Std_ReturnType"],
                    api_service_id=0x42, mandatory=False),
        ],
        det_errors=[
            DetErrorSpec(name="DCM_E_UNINIT", value=0x05),
            DetErrorSpec(name="DCM_E_PARAM", value=0x06),
            DetErrorSpec(name="DCM_E_PARAM_POINTER", value=0x07),
        ],
    )


def _comm_spec() -> ModuleSpec:
    return ModuleSpec(
        name="ComM",
        module_id=12,
        description="Communication Manager",
        layer="com",
        config_type="ComM_ConfigType",
        has_main_function=True,
        main_function_names=["ComM_MainFunction"],
        required_includes=["ComM_Types.h"],
        init_dependencies=["CanSM", "Nm"],
        apis=[
            ApiSpec(name="ComM_Init", return_type="void",
                    params=["const ComM_ConfigType*"], api_service_id=0x01),
            ApiSpec(name="ComM_DeInit", return_type="void",
                    params=[], api_service_id=0x02),
            ApiSpec(name="ComM_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x10),
            ApiSpec(name="ComM_MainFunction", return_type="void",
                    params=[], api_service_id=0x60),
            ApiSpec(name="ComM_RequestComMode", return_type="Std_ReturnType",
                    params=["ComM_UserHandleType", "ComM_ModeType"],
                    api_service_id=0x05),
        ],
        det_errors=[
            DetErrorSpec(name="COMM_E_UNINIT", value=0x01),
            DetErrorSpec(name="COMM_E_WRONG_PARAMETERS", value=0x02),
        ],
    )


def _cansm_spec() -> ModuleSpec:
    return ModuleSpec(
        name="CanSM",
        module_id=140,
        description="CAN State Manager",
        layer="com",
        config_type="CanSM_ConfigType",
        has_main_function=True,
        main_function_names=["CanSM_MainFunction"],
        required_includes=["CanSM_Types.h"],
        init_dependencies=["CanIf"],
        calls_to=["CanIf_SetControllerMode", "CanIf_SetPduMode",
                   "ComM_BusSM_ModeIndication"],
        called_by=["CanSM_ControllerBusOff", "CanSM_ControllerModeIndication"],
        apis=[
            ApiSpec(name="CanSM_Init", return_type="void",
                    params=["const CanSM_ConfigType*"], api_service_id=0x00),
            ApiSpec(name="CanSM_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x01),
            ApiSpec(name="CanSM_MainFunction", return_type="void",
                    params=[], api_service_id=0x05),
            ApiSpec(name="CanSM_RequestComMode", return_type="Std_ReturnType",
                    params=["NetworkHandleType", "ComM_ModeType"],
                    api_service_id=0x02),
            ApiSpec(name="CanSM_ControllerBusOff", return_type="void",
                    params=["uint8"], api_service_id=0x04),
            ApiSpec(name="CanSM_ControllerModeIndication", return_type="void",
                    params=["uint8", "CanIf_ControllerModeType"],
                    api_service_id=0x07),
        ],
        det_errors=[
            DetErrorSpec(name="CANSM_E_UNINIT", value=0x01),
            DetErrorSpec(name="CANSM_E_PARAM_POINTER", value=0x02),
            DetErrorSpec(name="CANSM_E_INVALID_NETWORK_HANDLE", value=0x03),
        ],
    )


def _get_call_relations() -> list[CallRelation]:
    """Define cross-module call relationships for AUTOSAR 4.0.3."""
    return [
        # TX path: Com -> PduR -> CanIf -> Can
        CallRelation("Com", "Com_SendSignal", "PduR", "PduR_ComTransmit", "tx",
                      "COM transmits I-PDU via PduR"),
        CallRelation("PduR", "PduR_ComTransmit", "CanIf", "CanIf_Transmit", "tx",
                      "PduR routes to CAN interface"),
        CallRelation("CanIf", "CanIf_Transmit", "Can", "Can_Write", "tx",
                      "CanIf writes to CAN driver"),
        # RX path: Can -> CanIf -> PduR -> Com
        CallRelation("Can", "Can_ISR/MainFunction", "CanIf", "CanIf_RxIndication", "rx",
                      "CAN driver indicates reception"),
        CallRelation("CanIf", "CanIf_RxIndication", "PduR", "PduR_CanIfRxIndication", "rx",
                      "CanIf forwards Rx to PduR"),
        CallRelation("PduR", "PduR_CanIfRxIndication", "Com", "Com_RxIndication", "rx",
                      "PduR delivers to COM"),
        # TX confirmation path
        CallRelation("Can", "Can_ISR", "CanIf", "CanIf_TxConfirmation", "tx",
                      "CAN driver confirms transmission"),
        CallRelation("CanIf", "CanIf_TxConfirmation", "PduR", "PduR_CanIfTxConfirmation", "tx",
                      "CanIf forwards TxConfirmation to PduR"),
        CallRelation("PduR", "PduR_CanIfTxConfirmation", "Com", "Com_TxConfirmation", "tx",
                      "PduR delivers TxConfirmation to COM"),
        # Diagnostic path
        CallRelation("Dcm", "Dcm_Internal", "PduR", "PduR_DcmTransmit", "tx",
                      "DCM transmits response via PduR"),
        # State management path
        CallRelation("CanIf", "CanIf_ControllerBusOff", "CanSM", "CanSM_ControllerBusOff", "rx",
                      "CanIf notifies CanSM of bus-off"),
        # Memory path
        CallRelation("NvM", "NvM_ReadBlock", "Fee", "Fee_Read", "tx",
                      "NvM reads via Fee"),
        CallRelation("Fee", "Fee_Internal", "Fls", "Fls_Read", "tx",
                      "Fee accesses Flash driver"),
        # Det reporting
        CallRelation("Com", "Com_*", "Det", "Det_ReportError", "tx",
                      "COM reports development errors"),
        CallRelation("PduR", "PduR_*", "Det", "Det_ReportError", "tx",
                      "PduR reports development errors"),
        CallRelation("CanIf", "CanIf_*", "Det", "Det_ReportError", "tx",
                      "CanIf reports development errors"),
    ]


def _get_init_order() -> list[str]:
    """Recommended BSW initialization order for AUTOSAR 4.0.3."""
    return [
        # Phase 1: MCAL & basic services
        "Det", "Os", "SchM",
        # Phase 2: MCAL drivers
        "Fls", "Can", "Spi", "Adc", "Dio", "Gpt", "Icu", "Pwm", "Port",
        # Phase 3: ECU Abstraction
        "Fee", "Ea", "CanIf", "LinIf",
        # Phase 4: Services
        "EcuM", "BswM", "NvM", "Dem",
        # Phase 5: Communication
        "PduR", "CanSM", "ComM", "Com", "Nm", "CanNm",
        # Phase 6: Diagnostics
        "Dcm", "FiM",
    ]


def get_spec() -> VersionSpec:
    """Get the complete AUTOSAR 4.0.3 specification."""
    modules = {}
    for factory in [_com_spec, _pdur_spec, _canif_spec, _can_spec,
                    _ecum_spec, _bswm_spec, _det_spec, _dem_spec,
                    _schm_spec, _os_spec, _nvm_spec, _fee_spec,
                    _fls_spec, _ea_spec, _dcm_spec, _comm_spec,
                    _cansm_spec]:
        spec = factory()
        modules[spec.name] = spec

    return VersionSpec(
        version="4.0.3",
        modules=modules,
        call_relations=_get_call_relations(),
        init_order=_get_init_order(),
    )
