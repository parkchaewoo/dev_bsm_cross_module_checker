#include "PduR.h"
#include "Com.h"
#include "CanIf.h"
#include "CanTp.h"
#include "Dcm.h"
#include "Det.h"

/* ===== Routing Function Pointer Tables ===== */
typedef Std_ReturnType (*PduR_IfTransmitFpType)(PduIdType, const PduInfoType*);
typedef void (*PduR_IfRxIndicationFpType)(PduIdType, const PduInfoType*);
typedef void (*PduR_IfTxConfirmationFpType)(PduIdType);

/* IF Transmit routing table: maps source PDU to destination lower layer */
static const PduR_IfTransmitFpType PduR_IfTxRoutingTable[] = {
    CanIf_Transmit,   /* Msg1 -> CanIf */
    CanIf_Transmit,   /* Msg2 -> CanIf */
    CanIf_Transmit,   /* Msg3 -> CanIf */
    CanIf_Transmit,   /* Msg4 -> CanIf */
    NULL_PTR,         /* Reserved */
    /* BUG: references non-existent function for diagnostic routing */
    SoAd_IfTransmit_NotExist,  /* Diag -> SoAd (FUNCTION DOES NOT EXIST) */
};

/* IF Rx Indication routing: maps source (CanIf) to destination (Com/Dcm) */
static const PduR_IfRxIndicationFpType PduR_IfRxRoutingTable[] = {
    Com_RxIndication,  /* Msg1 -> Com */
    Com_RxIndication,  /* Msg2 -> Com */
    Com_RxIndication,  /* Msg3 -> Com */
    Com_RxIndication,  /* Msg4 -> Com */
};

/* Tx Confirmation routing */
static const PduR_IfTxConfirmationFpType PduR_TxConfRoutingTable[] = {
    Com_TxConfirmation,   /* Msg1 -> Com */
    Com_TxConfirmation,   /* Msg2 -> Com */
    Com_TxConfirmation,   /* Msg3 -> Com */
    Com_TxConfirmation,   /* Msg4 -> Com */
};

static boolean PduR_InitStatus = FALSE;

void PduR_Init(const PduR_ConfigType* config)
{
    if (config == NULL_PTR)
    {
        Det_ReportError(PDUR_MODULE_ID, 0U, PDUR_SID_INIT, PDUR_E_INIT_FAILED);
        return;
    }
    PduR_InitStatus = TRUE;
}

void PduR_GetVersionInfo(Std_VersionInfoType* versioninfo)
{
    if (versioninfo == NULL_PTR)
    {
        Det_ReportError(PDUR_MODULE_ID, 0U, 0x02U, PDUR_E_PDU_ID_INVALID);
        return;
    }
}

Std_ReturnType PduR_ComTransmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr)
{
    if (PduR_InitStatus == FALSE)
    {
        Det_ReportError(PDUR_MODULE_ID, 0U, PDUR_SID_COMTRANSMIT, PDUR_E_UNINIT);
        return E_NOT_OK;
    }
    if (TxPduId >= 6U)
    {
        Det_ReportError(PDUR_MODULE_ID, 0U, PDUR_SID_COMTRANSMIT, PDUR_E_PDU_ID_INVALID);
        return E_NOT_OK;
    }

    /* Route to lower layer via function pointer table */
    if (PduR_IfTxRoutingTable[TxPduId] != NULL_PTR)
    {
        /* Map Com PDU ID to CanIf PDU ID via routing config */
        PduIdType destPduId = TxPduId; /* Simplified 1:1 mapping */
        return PduR_IfTxRoutingTable[TxPduId](destPduId, PduInfoPtr);
    }
    return E_NOT_OK;
}

Std_ReturnType PduR_DcmTransmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr)
{
    /* Route diagnostic PDUs to CanTp for segmented transmission */
    return CanTp_Transmit(TxPduId, PduInfoPtr);
}

void PduR_CanIfRxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr)
{
    if (PduR_InitStatus == FALSE)
    {
        Det_ReportError(PDUR_MODULE_ID, 0U, PDUR_SID_CANIF_RXIND, PDUR_E_UNINIT);
        return;
    }

    /* Route to upper layer (Com) */
    if (RxPduId < 4U)
    {
        Com_RxIndication(RxPduId, PduInfoPtr);
    }
    /* Diagnostic PDUs go to Dcm */
    else
    {
        Dcm_StartOfReception(RxPduId, PduInfoPtr, 0U, NULL_PTR);
    }
}

void PduR_CanIfTxConfirmation(PduIdType TxPduId)
{
    /* Route Tx confirmation to upper layer */
    Com_TxConfirmation(TxPduId);
}

/* TP Callbacks from CanTp */
BufReq_ReturnType PduR_CanTpStartOfReception(PduIdType id, const PduInfoType* info,
    PduLengthType TpSduLength, PduLengthType* bufferSizePtr)
{
    /* Forward to Dcm for diagnostic reception */
    return Dcm_StartOfReception(id, info, TpSduLength, bufferSizePtr);
}

BufReq_ReturnType PduR_CanTpCopyRxData(PduIdType id, const PduInfoType* info,
    PduLengthType* bufferSizePtr)
{
    return Dcm_CopyRxData(id, info, bufferSizePtr);
}

void PduR_CanTpRxIndication(PduIdType id, Std_ReturnType result)
{
    Dcm_TpRxIndication(id, result);
}

BufReq_ReturnType PduR_CanTpCopyTxData(PduIdType id, const PduInfoType* info,
    RetryInfoType* retry, PduLengthType* availableDataPtr)
{
    return Dcm_CopyTxData(id, info, retry, availableDataPtr);
}

void PduR_CanTpTxConfirmation(PduIdType id, Std_ReturnType result)
{
    Dcm_TpTxConfirmation(id, result);
}
