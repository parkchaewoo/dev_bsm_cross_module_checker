#ifndef CANIF_H
#define CANIF_H

#include "ComStack_Types.h"
#include "CanIf_Types.h"
#include "Can_GeneralTypes.h"
#include "CanIf_Cfg.h"

#define CANIF_MODULE_ID    60U

#define CANIF_E_PARAM_CANID        0x10U
#define CANIF_E_PARAM_DLC          0x11U
#define CANIF_E_PARAM_HRH          0x12U
#define CANIF_E_PARAM_LPDU         0x13U
#define CANIF_E_PARAM_CONTROLLER   0x14U
#define CANIF_E_UNINIT             0x30U

typedef uint8 CanIf_ControllerModeType;
typedef uint8 CanIf_PduModeType;
typedef uint8 CanIf_NotifStatusType;

typedef struct {
    uint8 CanIfMaxTxPduCfg;
    uint8 CanIfMaxRxPduCfg;
} CanIf_ConfigType;

extern void CanIf_Init(const CanIf_ConfigType* ConfigPtr);
extern void CanIf_GetVersionInfo(Std_VersionInfoType* VersionInfo);
extern Std_ReturnType CanIf_Transmit(PduIdType TxPduId, const PduInfoType* PduInfoPtr);
extern void CanIf_RxIndication(const Can_HwType* Mailbox, const PduInfoType* PduInfoPtr);
/* BUG: 4.4.0 requires 2 params (PduIdType, Std_ReturnType) */
extern void CanIf_TxConfirmation(PduIdType CanTxPduId);
extern void CanIf_ControllerBusOff(uint8 ControllerId);
extern void CanIf_ControllerModeIndication(uint8 ControllerId, CanIf_ControllerModeType ControllerMode);
extern Std_ReturnType CanIf_SetControllerMode(uint8 ControllerId, CanIf_ControllerModeType ControllerMode);
extern Std_ReturnType CanIf_GetControllerMode(uint8 ControllerId, CanIf_ControllerModeType* ControllerModePtr);
extern Std_ReturnType CanIf_SetPduMode(uint8 ControllerId, CanIf_PduModeType PduModeRequest);

#endif /* CANIF_H */
