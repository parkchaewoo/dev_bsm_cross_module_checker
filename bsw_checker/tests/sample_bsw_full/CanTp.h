#ifndef CANTP_H
#define CANTP_H

#include "ComStack_Types.h"
#include "CanTp_Types.h"

#define CANTP_MODULE_ID    35U

#define CANTP_E_UNINIT     0x20U
#define CANTP_E_PARAM_ID   0x02U

typedef struct {
    uint8 dummy;
} CanTp_ConfigType;

extern void CanTp_Init(const CanTp_ConfigType* CfgPtr);
extern Std_ReturnType CanTp_Transmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr);
/* BUG: CanTp_RxIndication is declared but NOT defined in CanTp.c */
extern void CanTp_RxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr);
extern void CanTp_TxConfirmation(PduIdType TxPduId, Std_ReturnType result);
extern void CanTp_MainFunction(void);

#endif /* CANTP_H */
