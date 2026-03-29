#include "CanIf.h"
#include "Can.h"
#include "PduR_CanIf.h"
#include "CanSM.h"
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

Std_ReturnType CanIf_Transmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr)
{
    Can_PduType canPdu;

    if (CanIf_InitStatus == FALSE)
    {
        Det_ReportError(CANIF_MODULE_ID, 0U, 0x05U, CANIF_E_UNINIT);
        return E_NOT_OK;
    }

    /* Map PDU to CAN HW handle and write */
    return Can_Write(0U, &canPdu);
}

void CanIf_RxIndication(const Can_HwType* Mailbox, const PduInfoType* PduInfoPtr)
{
    PduIdType rxPduId = 0U; /* Map from HRH */

    /* Forward to PduR */
    PduR_CanIfRxIndication(rxPduId, PduInfoPtr);
}

void CanIf_TxConfirmation(PduIdType CanTxPduId)
{
    PduR_CanIfTxConfirmation(CanTxPduId);
}

void CanIf_ControllerBusOff(uint8 ControllerId)
{
    CanSM_ControllerBusOff(ControllerId);
}

Std_ReturnType CanIf_SetControllerMode(uint8 ControllerId, CanIf_ControllerModeType ControllerMode)
{
    return E_OK;
}

Std_ReturnType CanIf_GetControllerMode(uint8 ControllerId, CanIf_ControllerModeType* ControllerModePtr)
{
    return E_OK;
}

Std_ReturnType CanIf_SetPduMode(uint8 ControllerId, CanIf_PduModeType PduModeRequest)
{
    return E_OK;
}
