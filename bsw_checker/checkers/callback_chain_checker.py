"""Callback Chain Checker - Validates end-to-end Tx/Rx/TP callback chains."""

import re
from collections import defaultdict

from ..parser.file_scanner import ScanResult
from .base_checker import BaseChecker, CheckerReport


class CallbackChainChecker(BaseChecker):
    name = "callback_chain_checker"
    description = "Validates end-to-end Tx/Rx/TP callback chains between BSW modules"

    # Full communication chains to validate
    TX_IF_CHAIN = [
        ("Com", "PduR_ComTransmit", "Com sends I-PDU via PduR"),
        ("PduR", "CanIf_Transmit", "PduR routes to CAN interface"),
        ("CanIf", "Can_Write", "CanIf writes to CAN driver"),
    ]
    RX_IF_CHAIN = [
        ("Can", "CanIf_RxIndication", "CAN driver notifies CanIf"),
        ("CanIf", "PduR_CanIfRxIndication", "CanIf forwards to PduR"),
        ("PduR", "Com_RxIndication", "PduR delivers to COM"),
    ]
    TX_CONF_CHAIN = [
        ("Can", "CanIf_TxConfirmation", "CAN driver confirms Tx"),
        ("CanIf", "PduR_CanIfTxConfirmation", "CanIf forwards TxConf to PduR"),
        ("PduR", "Com_TxConfirmation", "PduR delivers TxConf to COM"),
    ]
    TP_RX_CHAIN = [
        ("CanIf", "CanTp_RxIndication", "CanIf forwards TP frame to CanTp"),
        ("CanTp", "PduR_CanTpStartOfReception", "CanTp starts TP reception via PduR"),
        ("CanTp", "PduR_CanTpCopyRxData", "CanTp provides received data to PduR"),
        ("CanTp", "PduR_CanTpRxIndication", "CanTp signals reception complete"),
        ("PduR", "Dcm_StartOfReception", "PduR forwards to DCM"),
        ("PduR", "Dcm_CopyRxData", "PduR provides data to DCM"),
        ("PduR", "Dcm_TpRxIndication", "PduR signals complete to DCM"),
    ]
    TP_TX_CHAIN = [
        ("Dcm", "PduR_DcmTransmit", "DCM sends diagnostic response"),
        ("PduR", "CanTp_Transmit", "PduR routes to CanTp"),
        ("CanTp", "PduR_CanTpCopyTxData", "CanTp requests data from PduR"),
        ("CanTp", "CanIf_Transmit", "CanTp sends frames via CanIf"),
        ("CanTp", "PduR_CanTpTxConfirmation", "CanTp confirms Tx to PduR"),
        ("PduR", "Dcm_TpTxConfirmation", "PduR confirms Tx to DCM"),
    ]

    BUSOFF_CHAIN = [
        ("Can", "CanIf_ControllerBusOff", "CAN driver reports bus-off"),
        ("CanIf", "CanSM_ControllerBusOff", "CanIf notifies CanSM"),
        ("CanSM", "ComM_BusSM_ModeIndication", "CanSM notifies ComM"),
    ]

    MODE_CHAIN = [
        ("ComM", "CanSM_RequestComMode", "ComM requests CAN mode"),
        ("CanSM", "CanIf_SetControllerMode", "CanSM sets controller mode"),
        ("CanSM", "CanIf_SetPduMode", "CanSM sets PDU mode"),
    ]

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        chains = [
            ("IF-TX", self.TX_IF_CHAIN),
            ("IF-RX", self.RX_IF_CHAIN),
            ("IF-TXCONF", self.TX_CONF_CHAIN),
            ("TP-RX", self.TP_RX_CHAIN),
            ("TP-TX", self.TP_TX_CHAIN),
            ("BUSOFF", self.BUSOFF_CHAIN),
            ("MODE", self.MODE_CHAIN),
        ]

        for chain_name, chain_links in chains:
            self._validate_chain(scan_result, chain_name, chain_links)

        return self.report

    def _validate_chain(self, scan_result: ScanResult, chain_name: str,
                         chain_links: list[tuple[str, str, str]]):
        present = set(scan_result.modules.keys())
        missing_links = []
        ok_links = []

        for caller_mod, callee_func, desc in chain_links:
            if caller_mod not in present:
                continue

            found = False
            for pf in scan_result.modules[caller_mod].parsed_files:
                if callee_func in pf.raw_content:
                    found = True
                    break

            if found:
                ok_links.append((caller_mod, callee_func, desc))
            else:
                missing_links.append((caller_mod, callee_func, desc))

        total = len([l for l in chain_links if l[0] in present])
        if total == 0:
            return

        if not missing_links:
            self._pass("System", "CHAIN-001",
                       f"Chain {chain_name}: all {total} links OK",
                       f"Communication chain '{chain_name}' is complete. "
                       f"All {total} call links verified:\n" +
                       "\n".join(f"  {c} -> {f}(): {d}" for c, f, d in ok_links))
        else:
            for caller, callee, desc in missing_links:
                self._fail(caller, "CHAIN-002",
                           f"Chain {chain_name}: {caller} -> {callee}() missing",
                           f"Communication chain '{chain_name}' is broken. "
                           f"Module {caller} does not call {callee}(). "
                           f"Purpose: {desc}. "
                           f"This breaks the end-to-end data path. Messages sent "
                           f"through this chain will not reach their destination.",
                           suggestion=f"Add {callee}() call in {caller}.c, "
                                      f"or verify routing configuration")
