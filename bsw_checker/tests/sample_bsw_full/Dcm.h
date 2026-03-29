#ifndef DCM_H
#define DCM_H

#include "Dcm_Types.h"
#include "ComStack_Types.h"

#define DCM_MODULE_ID    53U

#define DCM_E_UNINIT          0x05U
#define DCM_E_PARAM           0x06U
#define DCM_E_PARAM_POINTER   0x07U

typedef uint8 Dcm_SecLevelType;
typedef uint8 Dcm_SesCtrlType;

typedef struct {
    uint8 DcmMaxProtocolCnt;
} Dcm_ConfigType;

extern void Dcm_Init(const Dcm_ConfigType* ConfigPtr);
extern void Dcm_GetVersionInfo(Std_VersionInfoType* versioninfo);
extern void Dcm_MainFunction(void);

/* TP Interface callbacks from PduR */
extern BufReq_ReturnType Dcm_StartOfReception(PduIdType id, const PduInfoType* info, PduLengthType TpSduLength, PduLengthType* bufferSizePtr);
extern BufReq_ReturnType Dcm_CopyRxData(PduIdType id, const PduInfoType* info, PduLengthType* bufferSizePtr);
extern void Dcm_TpRxIndication(PduIdType id, Std_ReturnType result);
extern BufReq_ReturnType Dcm_CopyTxData(PduIdType id, const PduInfoType* info, RetryInfoType* retry, PduLengthType* availableDataPtr);
extern void Dcm_TpTxConfirmation(PduIdType id, Std_ReturnType result);

#endif /* DCM_H */
