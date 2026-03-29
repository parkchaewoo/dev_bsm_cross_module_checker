#ifndef BSWM_H
#define BSWM_H

#include "BswM_Types.h"

#define BSWM_MODULE_ID    42U

#define BSWM_E_NULL_POINTER  0x04U
#define BSWM_E_UNINIT        0x01U
#define BSWM_E_PARAM_CONFIG  0x05U

typedef uint8 BswM_UserType;
typedef uint8 BswM_ModeType;

typedef struct {
    uint8 dummy;
} BswM_ConfigType;

extern void BswM_Init(const BswM_ConfigType* ConfigPtr);
extern void BswM_DeInit(void);
extern void BswM_MainFunction(void);
extern void BswM_RequestMode(BswM_UserType requesting_user, BswM_ModeType requested_mode);
extern void BswM_ComM_CurrentMode(NetworkHandleType Network, ComM_ModeType RequestedMode);

#endif /* BSWM_H */
