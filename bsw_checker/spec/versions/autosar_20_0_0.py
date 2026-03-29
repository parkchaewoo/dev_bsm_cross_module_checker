"""AUTOSAR 20.0.0 (R20-11, Classic & Adaptive merged release) BSW Module Specifications.

Changes from 4.9.0:
- New versioning scheme (20.0.0 = R20-11)
- Enhanced Ethernet/IP support
- Enhanced DoIP and SoAd
- GlobalTime modules
- Vehicle-to-X (V2X) support
- Enhanced CDD (Complex Device Driver) framework
"""

import copy
from .autosar_4_9_0 import get_spec as get_4_9_0_spec
from ..models import ApiSpec, DetErrorSpec, ModuleSpec, CallRelation, VersionSpec


def get_spec() -> VersionSpec:
    """Get AUTOSAR 20.0.0 spec by patching 4.9.0."""
    spec = copy.deepcopy(get_4_9_0_spec())
    spec.version = "20.0.0"

    # === Com enhancements ===
    if "Com" in spec.modules:
        com = spec.modules["Com"]
        com.apis.extend([
            ApiSpec(name="Com_GetConfigurationId", return_type="uint32",
                    params=[], api_service_id=0x08, mandatory=False,
                    since_version="20.0.0",
                    description="Get active configuration ID"),
            ApiSpec(name="Com_TriggerIPDUSend", return_type="void",
                    params=["PduIdType"],
                    api_service_id=0x17, mandatory=False, since_version="20.0.0"),
            ApiSpec(name="Com_TriggerIPDUSendWithMetaData", return_type="void",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x28, mandatory=False, since_version="20.0.0"),
        ])
        com.det_errors.append(
            DetErrorSpec(name="COM_E_SKIPPED_TRANSMISSION", value=0x05,
                         description="Transmission skipped (new in R20)")
        )

    # === Add SoAd module ===
    spec.modules["SoAd"] = ModuleSpec(
        name="SoAd",
        module_id=56,
        description="Socket Adaptor - TCP/IP socket abstraction",
        layer="com",
        config_type="SoAd_ConfigType",
        has_main_function=True,
        main_function_names=["SoAd_MainFunction"],
        required_includes=["SoAd_Types.h", "ComStack_Types.h"],
        init_dependencies=["TcpIp"],
        calls_to=["TcpIp_Bind", "TcpIp_TcpConnect", "TcpIp_UdpTransmit",
                   "PduR_SoAdRxIndication", "PduR_SoAdTxConfirmation"],
        called_by=["SoAd_RxIndication", "SoAd_TxConfirmation",
                    "SoAd_IfTransmit", "SoAd_TpTransmit"],
        apis=[
            ApiSpec(name="SoAd_Init", return_type="void",
                    params=["const SoAd_ConfigType*"], api_service_id=0x01,
                    since_version="4.0.3"),
            ApiSpec(name="SoAd_IfTransmit", return_type="Std_ReturnType",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x49, since_version="4.0.3"),
            ApiSpec(name="SoAd_TpTransmit", return_type="Std_ReturnType",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x4A, since_version="4.0.3"),
            ApiSpec(name="SoAd_RxIndication", return_type="void",
                    params=["TcpIp_SocketIdType", "const TcpIp_SockAddrType*",
                            "uint8*", "uint16"],
                    api_service_id=0x42, since_version="4.0.3"),
            ApiSpec(name="SoAd_MainFunction", return_type="void",
                    params=[], api_service_id=0x06, since_version="4.0.3"),
            ApiSpec(name="SoAd_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x02),
            ApiSpec(name="SoAd_OpenSoCon", return_type="Std_ReturnType",
                    params=["SoAd_SoConIdType"],
                    api_service_id=0x03, since_version="20.0.0"),
            ApiSpec(name="SoAd_CloseSoCon", return_type="Std_ReturnType",
                    params=["SoAd_SoConIdType", "boolean"],
                    api_service_id=0x04, since_version="20.0.0"),
        ],
        det_errors=[
            DetErrorSpec(name="SOAD_E_NOTINIT", value=0x01),
            DetErrorSpec(name="SOAD_E_PARAM_POINTER", value=0x02),
            DetErrorSpec(name="SOAD_E_INV_ARG", value=0x03),
            DetErrorSpec(name="SOAD_E_INV_SOCKETID", value=0x04),
        ],
    )

    # === Add TcpIp module ===
    spec.modules["TcpIp"] = ModuleSpec(
        name="TcpIp",
        module_id=170,
        description="TCP/IP Stack",
        layer="com",
        config_type="TcpIp_ConfigType",
        has_main_function=True,
        main_function_names=["TcpIp_MainFunction"],
        required_includes=["TcpIp_Types.h"],
        init_dependencies=["EthIf"],
        apis=[
            ApiSpec(name="TcpIp_Init", return_type="void",
                    params=["const TcpIp_ConfigType*"], api_service_id=0x01,
                    since_version="4.0.3"),
            ApiSpec(name="TcpIp_Bind", return_type="Std_ReturnType",
                    params=["TcpIp_SocketIdType", "TcpIp_LocalAddrIdType", "uint16*"],
                    api_service_id=0x05, since_version="4.0.3"),
            ApiSpec(name="TcpIp_UdpTransmit", return_type="Std_ReturnType",
                    params=["TcpIp_SocketIdType", "const uint8*", "const TcpIp_SockAddrType*", "uint16"],
                    api_service_id=0x07, since_version="4.0.3"),
            ApiSpec(name="TcpIp_TcpConnect", return_type="Std_ReturnType",
                    params=["TcpIp_SocketIdType", "const TcpIp_SockAddrType*"],
                    api_service_id=0x08, since_version="4.0.3"),
            ApiSpec(name="TcpIp_MainFunction", return_type="void",
                    params=[], api_service_id=0x06, since_version="4.0.3"),
        ],
        det_errors=[
            DetErrorSpec(name="TCPIP_E_NOTINIT", value=0x01),
            DetErrorSpec(name="TCPIP_E_PARAM_POINTER", value=0x02),
        ],
    )

    # === Add EthIf module ===
    spec.modules["EthIf"] = ModuleSpec(
        name="EthIf",
        module_id=65,
        description="Ethernet Interface",
        layer="com",
        config_type="EthIf_ConfigType",
        has_main_function=True,
        main_function_names=["EthIf_MainFunctionRx", "EthIf_MainFunctionTx"],
        required_includes=["EthIf_Types.h"],
        init_dependencies=["Eth"],
        apis=[
            ApiSpec(name="EthIf_Init", return_type="void",
                    params=["const EthIf_ConfigType*"], api_service_id=0x01),
            ApiSpec(name="EthIf_GetVersionInfo", return_type="void",
                    params=["Std_VersionInfoType*"], mandatory=False,
                    api_service_id=0x02),
            ApiSpec(name="EthIf_Transmit", return_type="Std_ReturnType",
                    params=["uint8", "Eth_BufIdxType", "Eth_FrameType",
                            "boolean", "uint16", "const uint8*"],
                    api_service_id=0x05),
            ApiSpec(name="EthIf_MainFunctionRx", return_type="void",
                    params=[], api_service_id=0x10),
            ApiSpec(name="EthIf_MainFunctionTx", return_type="void",
                    params=[], api_service_id=0x11),
        ],
        det_errors=[
            DetErrorSpec(name="ETHIF_E_NOT_INITIALIZED", value=0x01),
            DetErrorSpec(name="ETHIF_E_INV_CTRL_IDX", value=0x02),
        ],
    )

    # === Add DoIP module ===
    spec.modules["DoIP"] = ModuleSpec(
        name="DoIP",
        module_id=173,
        description="Diagnostics over IP",
        layer="com",
        config_type="DoIP_ConfigType",
        has_main_function=True,
        main_function_names=["DoIP_MainFunction"],
        required_includes=["DoIP_Types.h", "ComStack_Types.h"],
        init_dependencies=["SoAd"],
        calls_to=["SoAd_IfTransmit", "SoAd_TpTransmit",
                   "PduR_DoIPRxIndication", "PduR_DoIPTxConfirmation"],
        apis=[
            ApiSpec(name="DoIP_Init", return_type="void",
                    params=["const DoIP_ConfigType*"], api_service_id=0x01,
                    since_version="20.0.0"),
            ApiSpec(name="DoIP_MainFunction", return_type="void",
                    params=[], api_service_id=0x02, since_version="20.0.0"),
            ApiSpec(name="DoIP_TpTransmit", return_type="Std_ReturnType",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x49, since_version="20.0.0"),
        ],
        det_errors=[
            DetErrorSpec(name="DOIP_E_UNINIT", value=0x01),
            DetErrorSpec(name="DOIP_E_PARAM_POINTER", value=0x02),
        ],
    )

    # === Enhanced EcuM ===
    if "EcuM" in spec.modules:
        ecum = spec.modules["EcuM"]
        ecum.calls_to.extend(["SoAd_Init", "TcpIp_Init", "EthIf_Init", "DoIP_Init"])
        ecum.apis.append(
            ApiSpec(name="EcuM_GoHalt", return_type="Std_ReturnType",
                    params=[], api_service_id=0x1F, mandatory=False,
                    since_version="20.0.0")
        )
        ecum.apis.append(
            ApiSpec(name="EcuM_GoPoll", return_type="Std_ReturnType",
                    params=[], api_service_id=0x1E, mandatory=False,
                    since_version="20.0.0")
        )

    # === Enhanced PduR with Ethernet routing ===
    if "PduR" in spec.modules:
        pdur = spec.modules["PduR"]
        pdur.calls_to.extend(["SoAd_IfTransmit", "SoAd_TpTransmit",
                               "DoIP_TpTransmit"])
        pdur.called_by.extend(["PduR_SoAdRxIndication", "PduR_SoAdTxConfirmation",
                                "PduR_DoIPRxIndication", "PduR_DoIPTxConfirmation"])
        pdur.apis.extend([
            ApiSpec(name="PduR_SoAdRxIndication", return_type="void",
                    params=["PduIdType", "const PduInfoType*"],
                    api_service_id=0x42, mandatory=False, since_version="20.0.0"),
            ApiSpec(name="PduR_SoAdTxConfirmation", return_type="void",
                    params=["PduIdType", "Std_ReturnType"],
                    api_service_id=0x40, mandatory=False, since_version="20.0.0"),
        ])

    # Update init order
    spec.init_order.extend(["Eth", "EthIf", "TcpIp", "SoAd", "DoIP"])

    # Additional call relations
    spec.call_relations.extend([
        CallRelation("SoAd", "SoAd_IfTransmit", "TcpIp", "TcpIp_UdpTransmit", "tx",
                      "SoAd transmits via TCP/IP"),
        CallRelation("TcpIp", "TcpIp_RxIndication", "SoAd", "SoAd_RxIndication", "rx",
                      "TCP/IP forwards to SoAd"),
        CallRelation("DoIP", "DoIP_TpTransmit", "SoAd", "SoAd_TpTransmit", "tx",
                      "DoIP transmits via SoAd"),
        CallRelation("PduR", "PduR_DcmTransmit", "DoIP", "DoIP_TpTransmit", "tx",
                      "PduR routes DCM PDUs to DoIP"),
    ])

    return spec
