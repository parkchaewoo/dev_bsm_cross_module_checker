#ifndef COM_H
#define COM_H
#include "ComStack_Types.h"
#include "Com_Types.h"
#include "Com_Cfg.h"
typedef uint16 Com_SignalIdType;
typedef uint16 Com_IpduGroupIdType;
typedef struct { uint8 maxPdu; uint8 maxSig; } Com_ConfigType;
extern void Com_Init(const Com_ConfigType* config);
extern void Com_DeInit(void);
extern uint8 Com_SendSignal(Com_SignalIdType SignalId, const void* SignalDataPtr);
extern uint8 Com_ReceiveSignal(Com_SignalIdType SignalId, void* SignalDataPtr);
extern void Com_RxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr);
extern void Com_TxConfirmation(PduIdType TxPduId);
extern void Com_MainFunctionRx(void);
extern void Com_MainFunctionTx(void);
#endif
