#ifndef COM_H
#define COM_H

#include "ComStack_Types.h"
#include "Com_Types.h"
#include "Com_Cfg.h"

#define COM_MODULE_ID    50U

#define COM_SID_INIT                0x01U
#define COM_SID_DEINIT              0x02U
#define COM_SID_SEND_SIGNAL         0x0AU
#define COM_SID_RECEIVE_SIGNAL      0x0BU
#define COM_SID_MAIN_FUNCTION_RX    0x18U
#define COM_SID_MAIN_FUNCTION_TX    0x19U

#define COM_E_PARAM         0x01U
#define COM_E_UNINIT         0x02U
#define COM_E_PARAM_POINTER  0x03U

typedef uint16 Com_SignalIdType;
typedef uint16 Com_SignalGroupIdType;
typedef uint16 Com_IpduGroupIdType;
typedef uint8 Com_StatusType;

typedef struct {
    uint8 ComMaxIPduCnt;
    uint8 ComMaxSignalCnt;
} Com_ConfigType;

extern void Com_Init(const Com_ConfigType* config);
extern void Com_DeInit(void);
extern void Com_GetVersionInfo(Std_VersionInfoType* versioninfo);
extern uint8 Com_SendSignal(Com_SignalIdType SignalId, const void* SignalDataPtr);
extern uint8 Com_ReceiveSignal(Com_SignalIdType SignalId, void* SignalDataPtr);
extern uint8 Com_SendSignalGroup(Com_SignalGroupIdType SignalGroupId);
extern uint8 Com_ReceiveSignalGroup(Com_SignalGroupIdType SignalGroupId);
extern void Com_MainFunctionRx(void);
extern void Com_MainFunctionTx(void);
extern void Com_MainFunctionRouteSignals(void);

/* Callbacks from PduR */
extern void Com_RxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr);
/* BUG: 4.4.0 requires (PduIdType, Std_ReturnType) but only has 1 param */
extern void Com_TxConfirmation(PduIdType TxPduId);
extern Std_ReturnType Com_TriggerTransmit(PduIdType TxPduId, PduInfoType* PduInfoPtr);

extern void Com_IpduGroupStart(Com_IpduGroupIdType IpduGroupId, boolean initialize);
extern void Com_IpduGroupStop(Com_IpduGroupIdType IpduGroupId);

#endif /* COM_H */
