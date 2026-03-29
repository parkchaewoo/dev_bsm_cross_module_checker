#include "Dcm.h"
#include "PduR.h"
#include "Dem.h"
#include "Det.h"

static boolean Dcm_InitStatus = FALSE;

void Dcm_Init(const Dcm_ConfigType* ConfigPtr)
{
    if (ConfigPtr == NULL_PTR)
    {
        Det_ReportError(DCM_MODULE_ID, 0U, 0x01U, DCM_E_PARAM_POINTER);
        return;
    }
    Dcm_InitStatus = TRUE;
}

void Dcm_MainFunction(void)
{
    if (Dcm_InitStatus == FALSE) return;

    /* Process pending diagnostic requests */
    /* Send responses via PduR_DcmTransmit */
    PduInfoType responseInfo;
    responseInfo.SduLength = 8U;
    responseInfo.SduDataPtr = NULL_PTR;
    PduR_DcmTransmit(0U, &responseInfo);
}

BufReq_ReturnType Dcm_StartOfReception(PduIdType id, const PduInfoType* info,
    PduLengthType TpSduLength, PduLengthType* bufferSizePtr)
{
    if (bufferSizePtr == NULL_PTR) return BUFREQ_E_NOT_OK;
    *bufferSizePtr = 4095U;
    return BUFREQ_OK;
}

BufReq_ReturnType Dcm_CopyRxData(PduIdType id, const PduInfoType* info,
    PduLengthType* bufferSizePtr)
{
    if (info == NULL_PTR || bufferSizePtr == NULL_PTR) return BUFREQ_E_NOT_OK;
    *bufferSizePtr = 4095U;
    return BUFREQ_OK;
}

void Dcm_TpRxIndication(PduIdType id, Std_ReturnType result)
{
    if (result == E_OK)
    {
        /* Process complete diagnostic request */
        /* Report DTC status via Dem */
        Dem_SetEventStatus(0U, DEM_EVENT_STATUS_PASSED);
    }
}

BufReq_ReturnType Dcm_CopyTxData(PduIdType id, const PduInfoType* info,
    RetryInfoType* retry, PduLengthType* availableDataPtr)
{
    if (availableDataPtr == NULL_PTR) return BUFREQ_E_NOT_OK;
    return BUFREQ_OK;
}

void Dcm_TpTxConfirmation(PduIdType id, Std_ReturnType result)
{
    /* Response transmission complete */
}
