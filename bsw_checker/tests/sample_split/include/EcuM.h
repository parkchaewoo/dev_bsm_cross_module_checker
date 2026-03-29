#ifndef ECUM_H
#define ECUM_H

#include "EcuM_Types.h"

#define ECUM_MODULE_ID    10U

#define ECUM_E_UNINIT           0x10U
#define ECUM_E_SERVICE_DISABLED 0x11U
#define ECUM_E_NULL_POINTER     0x12U
#define ECUM_E_INVALID_PAR      0x13U

typedef uint8 EcuM_StateType;
typedef uint8 EcuM_UserType;
typedef uint32 EcuM_WakeupSourceType;

typedef struct {
    uint8 EcuMMaxSleepModeCnt;
} EcuM_ConfigType;

extern void EcuM_Init(void);
extern void EcuM_StartupTwo(void);
extern void EcuM_Shutdown(void);
extern void EcuM_MainFunction(void);
extern Std_ReturnType EcuM_GetState(EcuM_StateType* state);
extern Std_ReturnType EcuM_RequestRUN(EcuM_UserType user);
extern Std_ReturnType EcuM_ReleaseRUN(EcuM_UserType user);
extern void EcuM_SetWakeupEvent(EcuM_WakeupSourceType sources);

#endif /* ECUM_H */
