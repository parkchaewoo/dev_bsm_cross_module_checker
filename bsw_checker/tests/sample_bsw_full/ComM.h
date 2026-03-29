#ifndef COMM_H
#define COMM_H

#include "ComM_Types.h"

#define COMM_MODULE_ID    12U

#define COMM_E_UNINIT              0x01U
#define COMM_E_WRONG_PARAMETERS    0x02U

typedef uint8 ComM_UserHandleType;
typedef uint8 ComM_ModeType;

#define COMM_NO_COMMUNICATION    0x00U
#define COMM_SILENT_COMMUNICATION 0x01U
#define COMM_FULL_COMMUNICATION  0x02U

typedef struct {
    uint8 ComMMaxChannelCnt;
} ComM_ConfigType;

extern void ComM_Init(const ComM_ConfigType* ConfigPtr);
extern void ComM_DeInit(void);
extern void ComM_GetVersionInfo(Std_VersionInfoType* VersionInfo);
extern void ComM_MainFunction(void);
extern Std_ReturnType ComM_RequestComMode(ComM_UserHandleType User, ComM_ModeType ComMode);
extern Std_ReturnType ComM_GetCurrentComMode(ComM_UserHandleType User, ComM_ModeType* ComModePtr);
extern void ComM_BusSM_ModeIndication(NetworkHandleType Channel, ComM_ModeType ComMode);
extern void ComM_CommunicationAllowed(NetworkHandleType Channel, boolean Allowed);

#endif /* COMM_H */
