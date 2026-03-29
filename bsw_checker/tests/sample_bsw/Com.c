#include "Com.h"
#include "PduR_Com.h"
#include "Det.h"
#include "SchM_Com.h"

static boolean Com_InitStatus = FALSE;

void Com_Init(const Com_ConfigType* config)
{
    if (config == NULL_PTR)
    {
        Det_ReportError(COM_MODULE_ID, 0U, COM_SID_INIT, COM_E_PARAM_POINTER);
        return;
    }
    Com_InitStatus = TRUE;
}

void Com_DeInit(void)
{
    Com_InitStatus = FALSE;
}

uint8 Com_SendSignal(Com_SignalIdType SignalId, const void* SignalDataPtr)
{
    PduInfoType pduInfo;
    Std_ReturnType ret;

    if (Com_InitStatus == FALSE)
    {
        Det_ReportError(COM_MODULE_ID, 0U, COM_SID_SEND_SIGNAL, COM_E_UNINIT);
        return COM_SERVICE_NOT_AVAILABLE;
    }

    /* Pack signal into I-PDU buffer */
    /* ... */

    /* Trigger transmission via PduR */
    ret = PduR_ComTransmit(ComConf_ComIPdu_Msg1_Tx, &pduInfo);

    return E_OK;
}

uint8 Com_ReceiveSignal(Com_SignalIdType SignalId, void* SignalDataPtr)
{
    if (Com_InitStatus == FALSE)
    {
        Det_ReportError(COM_MODULE_ID, 0U, COM_SID_RECEIVE_SIGNAL, COM_E_UNINIT);
        return COM_SERVICE_NOT_AVAILABLE;
    }
    return E_OK;
}

void Com_RxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr)
{
    /* Process received I-PDU */
}

void Com_TxConfirmation(PduIdType TxPduId)
{
    /* Handle Tx confirmation */
}

Std_ReturnType Com_TriggerTransmit(PduIdType TxPduId, PduInfoType* PduInfoPtr)
{
    return E_OK;
}

void Com_MainFunctionRx(void)
{
    /* Periodic Rx processing */
}

void Com_MainFunctionTx(void)
{
    /* Periodic Tx processing */
}
