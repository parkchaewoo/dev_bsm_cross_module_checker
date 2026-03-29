#ifndef COM_H
#define COM_H

#include "ComStack_Types.h"
#include "Com_Types.h"
#include "Com_Cfg.h"

/* Module ID */
#define COM_MODULE_ID    50U

/* API Service IDs */
#define COM_SID_INIT                0x01U
#define COM_SID_DEINIT              0x02U
#define COM_SID_SEND_SIGNAL         0x0AU
#define COM_SID_RECEIVE_SIGNAL      0x0BU

/* DET Error Codes */
#define COM_E_PARAM         0x01U
#define COM_E_UNINIT         0x02U
#define COM_E_PARAM_POINTER  0x03U

/* Type definitions */
typedef uint16 Com_SignalIdType;
typedef uint16 Com_IpduGroupIdType;
typedef struct {
    uint8 dummy;
} Com_ConfigType;

/* API declarations */
extern void Com_Init(const Com_ConfigType* config);
extern void Com_DeInit(void);
extern void Com_GetVersionInfo(Std_VersionInfoType* versioninfo);
extern uint8 Com_SendSignal(Com_SignalIdType SignalId, const void* SignalDataPtr);
extern uint8 Com_ReceiveSignal(Com_SignalIdType SignalId, void* SignalDataPtr);
extern void Com_MainFunctionRx(void);
extern void Com_MainFunctionTx(void);

/* Callback declarations */
extern void Com_RxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr);
extern void Com_TxConfirmation(PduIdType TxPduId);
extern Std_ReturnType Com_TriggerTransmit(PduIdType TxPduId, PduInfoType* PduInfoPtr);

extern void Com_IpduGroupStart(Com_IpduGroupIdType IpduGroupId, boolean initialize);
extern void Com_IpduGroupStop(Com_IpduGroupIdType IpduGroupId);

#endif /* COM_H */
