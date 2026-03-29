#ifndef NVM_H
#define NVM_H

#include "NvM_Types.h"

#define NVM_MODULE_ID    20U

#define NVM_E_PARAM_BLOCK_ID    0x0AU
#define NVM_E_PARAM_BLOCK_TYPE  0x0BU
#define NVM_E_NOT_INITIALIZED   0x14U

typedef uint16 NvM_BlockIdType;

typedef struct {
    uint16 NvMMaxBlockCnt;
} NvM_ConfigType;

extern void NvM_Init(void);
extern void NvM_GetVersionInfo(Std_VersionInfoType* versioninfo);
extern Std_ReturnType NvM_ReadBlock(NvM_BlockIdType BlockId, void* NvM_DstPtr);
extern Std_ReturnType NvM_WriteBlock(NvM_BlockIdType BlockId, const void* NvM_SrcPtr);
extern void NvM_ReadAll(void);
extern void NvM_WriteAll(void);
extern void NvM_MainFunction(void);

#endif /* NVM_H */
