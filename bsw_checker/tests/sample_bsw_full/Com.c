#include "Com.h"
#include "PduR_Com.h"
#include "Det.h"
#include "SchM_Com.h"
#include "Dem.h"

static boolean Com_InitStatus = FALSE;
static Com_ConfigType Com_CurrentConfig;

void Com_Init(const Com_ConfigType* config)
{
    if (config == NULL_PTR)
    {
        Det_ReportError(COM_MODULE_ID, 0U, COM_SID_INIT, COM_E_PARAM_POINTER);
        return;
    }
    Com_CurrentConfig = *config;
    Com_InitStatus = TRUE;
}

void Com_DeInit(void)
{
    Com_InitStatus = FALSE;
}

void Com_GetVersionInfo(Std_VersionInfoType* versioninfo)
{
    if (versioninfo == NULL_PTR)
    {
        Det_ReportError(COM_MODULE_ID, 0U, 0x09U, COM_E_PARAM_POINTER);
        return;
    }
    versioninfo->vendorID = 0x0001U;
    versioninfo->moduleID = COM_MODULE_ID;
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
    if (SignalDataPtr == NULL_PTR)
    {
        Det_ReportError(COM_MODULE_ID, 0U, COM_SID_SEND_SIGNAL, COM_E_PARAM_POINTER);
        return COM_SERVICE_NOT_AVAILABLE;
    }

    SchM_Enter_Com_COM_EXCLUSIVE_AREA_0();
    /* Pack signal into I-PDU buffer */
    pduInfo.SduLength = 8U;
    pduInfo.SduDataPtr = NULL_PTR;
    SchM_Exit_Com_COM_EXCLUSIVE_AREA_0();

    /* Transmit via PduR - uses PDU IDs from Com_Cfg.h */
    if (SignalId < 3U)
    {
        ret = PduR_ComTransmit(ComConf_ComIPdu_Msg1_Tx, &pduInfo);
    }
    else if (SignalId < 6U)
    {
        ret = PduR_ComTransmit(ComConf_ComIPdu_Msg2_Tx, &pduInfo);
    }
    else
    {
        /* BUG: Msg3_Tx PDU ID = 0x05 in Com, but 0x06 in PduR! */
        ret = PduR_ComTransmit(ComConf_ComIPdu_Msg3_Tx, &pduInfo);
    }

    return (ret == E_OK) ? COM_OK : COM_BUSY;
}

uint8 Com_ReceiveSignal(Com_SignalIdType SignalId, void* SignalDataPtr)
{
    if (Com_InitStatus == FALSE)
    {
        Det_ReportError(COM_MODULE_ID, 0U, COM_SID_RECEIVE_SIGNAL, COM_E_UNINIT);
        return COM_SERVICE_NOT_AVAILABLE;
    }

    SchM_Enter_Com_COM_EXCLUSIVE_AREA_1();
    /* Unpack signal from I-PDU buffer */
    SchM_Exit_Com_COM_EXCLUSIVE_AREA_1();

    return E_OK;
}

uint8 Com_SendSignalGroup(Com_SignalGroupIdType SignalGroupId)
{
    return E_OK;
}

uint8 Com_ReceiveSignalGroup(Com_SignalGroupIdType SignalGroupId)
{
    return E_OK;
}

void Com_RxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr)
{
    if (PduInfoPtr == NULL_PTR)
    {
        return;
    }
    /* Process received I-PDU and update signal buffers */
    switch (RxPduId)
    {
        case ComConf_ComIPdu_Msg1_Rx:
            /* Unpack Msg1 signals */
            break;
        case ComConf_ComIPdu_Msg2_Rx:
            /* Unpack Msg2 signals */
            break;
        case ComConf_ComIPdu_Msg3_Rx:
            /* Unpack Msg3 signals */
            break;
        case ComConf_ComIPdu_Diag_Rx:
            /* Unpack diagnostic signals */
            break;
        default:
            Det_ReportError(COM_MODULE_ID, 0U, 0x42U, COM_E_PARAM);
            break;
    }
}

void Com_TxConfirmation(PduIdType TxPduId)
{
    /* Handle Tx confirmation - signal Tx done */
}

Std_ReturnType Com_TriggerTransmit(PduIdType TxPduId, PduInfoType* PduInfoPtr)
{
    if (PduInfoPtr == NULL_PTR)
    {
        return E_NOT_OK;
    }
    return E_OK;
}

void Com_MainFunctionRx(void)
{
    if (Com_InitStatus == FALSE) return;
    /* Periodic Rx processing: deadline monitoring, signal timeout */
}

void Com_MainFunctionTx(void)
{
    if (Com_InitStatus == FALSE) return;
    /* Periodic Tx processing: cyclic send, minimum delay */
    PduInfoType pduInfo;
    pduInfo.SduLength = 8U;
    pduInfo.SduDataPtr = NULL_PTR;

    /* Cyclic transmission of Msg1 */
    PduR_ComTransmit(ComConf_ComIPdu_Msg1_Tx, &pduInfo);
}

void Com_MainFunctionRouteSignals(void)
{
    /* Signal gateway routing */
}

void Com_IpduGroupStart(Com_IpduGroupIdType IpduGroupId, boolean initialize)
{
}

void Com_IpduGroupStop(Com_IpduGroupIdType IpduGroupId)
{
}
