#include "CanIf.h"
#include "Can.h"
#include "PduR_CanIf.h"
#include "CanSM.h"
#include "CanTp.h"
#include "Det.h"

static boolean CanIf_InitStatus = FALSE;

void CanIf_Init(const CanIf_ConfigType* ConfigPtr)
{
    if (ConfigPtr == NULL_PTR)
    {
        Det_ReportError(CANIF_MODULE_ID, 0U, 0x01U, CANIF_E_PARAM_LPDU);
        return;
    }
    CanIf_InitStatus = TRUE;
}

void CanIf_GetVersionInfo(Std_VersionInfoType* VersionInfo)
{
    if (VersionInfo == NULL_PTR)
    {
        Det_ReportError(CANIF_MODULE_ID, 0U, 0x0BU, CANIF_E_PARAM_LPDU);
        return;
    }
}

Std_ReturnType CanIf_Transmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr)
{
    Can_PduType canPdu;
    Can_ReturnType canRet;

    if (CanIf_InitStatus == FALSE)
    {
        Det_ReportError(CANIF_MODULE_ID, 0U, 0x05U, CANIF_E_UNINIT);
        return E_NOT_OK;
    }
    if (PduInfoPtr == NULL_PTR)
    {
        Det_ReportError(CANIF_MODULE_ID, 0U, 0x05U, CANIF_E_PARAM_LPDU);
        return E_NOT_OK;
    }

    /* DLC check */
    if (PduInfoPtr->SduLength > 64U)
    {
        Det_ReportError(CANIF_MODULE_ID, 0U, 0x05U, CANIF_E_PARAM_DLC);
        return E_NOT_OK;
    }

    /* Map PDU to CAN HW Object Handle and write to CAN driver */
    canPdu.id = (Can_IdType)TxPduId;
    canPdu.swPduHandle = TxPduId;
    canPdu.length = (uint8)PduInfoPtr->SduLength;
    canPdu.sdu = PduInfoPtr->SduDataPtr;

    canRet = Can_Write(0U, &canPdu);

    return (canRet == CAN_OK) ? E_OK : E_NOT_OK;
}

void CanIf_RxIndication(const Can_HwType* Mailbox, const PduInfoType* PduInfoPtr)
{
    PduIdType rxPduId;

    if (CanIf_InitStatus == FALSE)
    {
        return;
    }

    /* Map HRH (Hardware Receive Handle) to software PDU ID */
    rxPduId = (PduIdType)Mailbox->hoh;

    /* Route to PduR for IF-type PDUs */
    if (rxPduId < 0x10U)
    {
        PduR_CanIfRxIndication(rxPduId + 0x10U, PduInfoPtr);
    }
    /* Route TP frames to CanTp */
    else if (rxPduId >= 0x20U)
    {
        CanTp_RxIndication(rxPduId, PduInfoPtr);
    }
}

void CanIf_TxConfirmation(PduIdType CanTxPduId)
{
    if (CanIf_InitStatus == FALSE) return;

    /* Notify PduR of successful transmission */
    PduR_CanIfTxConfirmation(CanTxPduId);
}

void CanIf_ControllerBusOff(uint8 ControllerId)
{
    /* Notify CanSM of bus-off event */
    CanSM_ControllerBusOff(ControllerId);
}

void CanIf_ControllerModeIndication(uint8 ControllerId, CanIf_ControllerModeType ControllerMode)
{
    CanSM_ControllerModeIndication(ControllerId, ControllerMode);
}

Std_ReturnType CanIf_SetControllerMode(uint8 ControllerId, CanIf_ControllerModeType ControllerMode)
{
    return Can_SetControllerMode(ControllerId, (Can_StateTransitionType)ControllerMode);
}

Std_ReturnType CanIf_GetControllerMode(uint8 ControllerId, CanIf_ControllerModeType* ControllerModePtr)
{
    if (ControllerModePtr == NULL_PTR) return E_NOT_OK;
    return E_OK;
}

Std_ReturnType CanIf_SetPduMode(uint8 ControllerId, CanIf_PduModeType PduModeRequest)
{
    return E_OK;
}
