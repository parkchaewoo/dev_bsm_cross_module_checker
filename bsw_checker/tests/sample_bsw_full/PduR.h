#ifndef PDUR_H
#define PDUR_H

#include "ComStack_Types.h"
#include "PduR_Types.h"
#include "PduR_Cfg.h"

#define PDUR_MODULE_ID    51U

#define PDUR_SID_INIT              0x01U
#define PDUR_SID_COMTRANSMIT       0x49U
#define PDUR_SID_CANIF_RXIND       0x42U
#define PDUR_SID_CANIF_TXCONF      0x40U

#define PDUR_E_INIT_FAILED       0x00U
#define PDUR_E_UNINIT            0x01U
#define PDUR_E_PDU_ID_INVALID    0x02U
#define PDUR_E_TP_TX_REQ_REJECTED 0x03U

typedef struct {
    uint16 PduRMaxRoutingPathCnt;
    boolean PduRDevErrorDetect;
} PduR_ConfigType;

extern void PduR_Init(const PduR_ConfigType* config);
extern void PduR_GetVersionInfo(Std_VersionInfoType* versioninfo);

/* Upper layer APIs */
extern Std_ReturnType PduR_ComTransmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr);
extern Std_ReturnType PduR_DcmTransmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr);

/* Lower layer callbacks from CanIf */
extern void PduR_CanIfRxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr);
extern void PduR_CanIfTxConfirmation(PduIdType TxPduId);

/* TP callbacks from CanTp */
extern BufReq_ReturnType PduR_CanTpStartOfReception(PduIdType id, const PduInfoType* info, PduLengthType TpSduLength, PduLengthType* bufferSizePtr);
extern BufReq_ReturnType PduR_CanTpCopyRxData(PduIdType id, const PduInfoType* info, PduLengthType* bufferSizePtr);
extern void PduR_CanTpRxIndication(PduIdType id, Std_ReturnType result);
extern BufReq_ReturnType PduR_CanTpCopyTxData(PduIdType id, const PduInfoType* info, RetryInfoType* retry, PduLengthType* availableDataPtr);
extern void PduR_CanTpTxConfirmation(PduIdType id, Std_ReturnType result);

#endif /* PDUR_H */
