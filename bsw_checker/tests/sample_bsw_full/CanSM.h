#ifndef CANSM_H
#define CANSM_H

#include "CanSM_Types.h"
#include "ComM_Types.h"

/* BUG: Wrong Module ID! AUTOSAR says 140 for CanSM */
#define CANSM_MODULE_ID    99U

#define CANSM_E_UNINIT                    0x01U
#define CANSM_E_PARAM_POINTER             0x02U
#define CANSM_E_INVALID_NETWORK_HANDLE    0x03U

typedef uint8 NetworkHandleType;

typedef struct {
    uint8 CanSMMaxNetworkCnt;
} CanSM_ConfigType;

extern void CanSM_Init(const CanSM_ConfigType* ConfigPtr);
extern void CanSM_GetVersionInfo(Std_VersionInfoType* VersionInfo);
extern void CanSM_MainFunction(void);
extern Std_ReturnType CanSM_RequestComMode(NetworkHandleType network, ComM_ModeType ComMode);
extern void CanSM_ControllerBusOff(uint8 ControllerId);
extern void CanSM_ControllerModeIndication(uint8 ControllerId, CanIf_ControllerModeType ControllerMode);

#endif /* CANSM_H */
