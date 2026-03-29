#ifndef CANIF_H
#define CANIF_H
#include "ComStack_Types.h"
#include "Can_GeneralTypes.h"
typedef struct { uint8 dummy; } CanIf_ConfigType;
extern void CanIf_Init(const CanIf_ConfigType* cfg);
extern Std_ReturnType CanIf_Transmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr);
extern void CanIf_RxIndication(const Can_HwType* Mailbox, const PduInfoType* PduInfoPtr);
extern void CanIf_TxConfirmation(PduIdType TxPduId);
#endif
