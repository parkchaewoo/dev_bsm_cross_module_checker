#include "PduR.h"
#include "Com.h"
#include "CanIf.h"
#include "Det.h"

/* Routing function pointer table */
typedef Std_ReturnType (*PduR_LoTpTransmitFuncType)(PduIdType, const PduInfoType*);

static const PduR_LoTpTransmitFuncType PduR_TxRoutingTable[] = {
    CanIf_Transmit,
    CanIf_Transmit,
};

static boolean PduR_InitStatus = FALSE;

void PduR_Init(const PduR_ConfigType* config)
{
    if (config == NULL_PTR)
    {
        Det_ReportError(PDUR_MODULE_ID, 0U, 0x01U, PDUR_E_INIT_FAILED);
        return;
    }
    PduR_InitStatus = TRUE;
}

Std_ReturnType PduR_ComTransmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr)
{
    if (PduR_InitStatus == FALSE)
    {
        Det_ReportError(PDUR_MODULE_ID, 0U, 0x49U, PDUR_E_UNINIT);
        return E_NOT_OK;
    }

    /* Route to CanIf */
    return CanIf_Transmit(TxPduId, PduInfoPtr);
}

Std_ReturnType PduR_DcmTransmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr)
{
    return CanIf_Transmit(TxPduId, PduInfoPtr);
}

void PduR_CanIfRxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr)
{
    /* Route received PDU to upper layer (Com) */
    Com_RxIndication(RxPduId, PduInfoPtr);
}

void PduR_CanIfTxConfirmation(PduIdType TxPduId)
{
    Com_TxConfirmation(TxPduId);
}
