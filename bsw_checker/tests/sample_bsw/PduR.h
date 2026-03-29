#ifndef PDUR_H
#define PDUR_H

#include "ComStack_Types.h"
#include "PduR_Types.h"
#include "PduR_Cfg.h"

#define PDUR_MODULE_ID    51U

/* DET Error Codes */
#define PDUR_E_INIT_FAILED       0x00U
#define PDUR_E_UNINIT            0x01U
#define PDUR_E_PDU_ID_INVALID    0x02U
#define PDUR_E_TP_TX_REQ_REJECTED 0x03U

typedef struct {
    uint8 dummy;
} PduR_ConfigType;

extern void PduR_Init(const PduR_ConfigType* config);
extern void PduR_GetVersionInfo(Std_VersionInfoType* versioninfo);

/* Upper layer API (called by Com) */
extern Std_ReturnType PduR_ComTransmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr);
extern Std_ReturnType PduR_DcmTransmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr);

/* Lower layer callbacks (called by CanIf) */
extern void PduR_CanIfRxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr);
extern void PduR_CanIfTxConfirmation(PduIdType TxPduId);

#endif /* PDUR_H */
