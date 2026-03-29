#include "CanTp.h"
#include "CanIf.h"
#include "PduR.h"
#include "Det.h"

static boolean CanTp_InitStatus = FALSE;

void CanTp_Init(const CanTp_ConfigType* CfgPtr)
{
    if (CfgPtr == NULL_PTR)
    {
        Det_ReportError(CANTP_MODULE_ID, 0U, 0x01U, CANTP_E_PARAM_ID);
        return;
    }
    CanTp_InitStatus = TRUE;
}

Std_ReturnType CanTp_Transmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr)
{
    if (CanTp_InitStatus == FALSE)
    {
        Det_ReportError(CANTP_MODULE_ID, 0U, 0x49U, CANTP_E_UNINIT);
        return E_NOT_OK;
    }

    /* Send First Frame via CanIf */
    PduInfoType ffInfo;
    ffInfo.SduLength = 8U;
    ffInfo.SduDataPtr = NULL_PTR;
    return CanIf_Transmit(TxPduId, &ffInfo);
}

/* BUG: CanTp_RxIndication is declared in header but NOT defined here!
 * This means CanIf cannot call back into CanTp for TP frame reception.
 * This is an intentional missing callback to test detection. */

void CanTp_TxConfirmation(PduIdType TxPduId, Std_ReturnType result)
{
    /* Handle Tx confirmation, send next CF */
    if (result == E_OK)
    {
        /* Continue sending Consecutive Frames */
        PduR_CanTpTxConfirmation(TxPduId, E_OK);
    }
}

void CanTp_MainFunction(void)
{
    if (CanTp_InitStatus == FALSE) return;

    /* Timeout monitoring for N_Ar, N_Br, N_Cr timers */
    /* Send pending Consecutive Frames */
    /* Request buffer from PduR: PduR_CanTpCopyTxData */
    PduLengthType available = 0;
    PduInfoType info;
    info.SduLength = 7U;
    info.SduDataPtr = NULL_PTR;
    PduR_CanTpCopyTxData(0U, &info, NULL_PTR, &available);

    /* Provide received data to PduR: PduR_CanTpCopyRxData */
    PduLengthType bufSize = 0;
    PduR_CanTpCopyRxData(0U, &info, &bufSize);
}
