#ifndef PDUR_H
#define PDUR_H
#include "ComStack_Types.h"
#include "PduR_Types.h"
typedef struct { uint16 maxPath; } PduR_ConfigType;
extern void PduR_Init(const PduR_ConfigType* config);
extern Std_ReturnType PduR_ComTransmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr);
extern void PduR_CanIfRxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr);
extern void PduR_CanIfTxConfirmation(PduIdType TxPduId);
#endif
