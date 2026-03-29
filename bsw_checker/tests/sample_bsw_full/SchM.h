#ifndef SCHM_H
#define SCHM_H

#include "Std_Types.h"

#define SCHM_MODULE_ID    130U

extern void SchM_Init(void);
extern void SchM_DeInit(void);

/* Exclusive area enter/exit macros (per-module) */
#define SchM_Enter_Com_COM_EXCLUSIVE_AREA_0()
#define SchM_Exit_Com_COM_EXCLUSIVE_AREA_0()
#define SchM_Enter_Com_COM_EXCLUSIVE_AREA_1()
#define SchM_Exit_Com_COM_EXCLUSIVE_AREA_1()
#define SchM_Enter_NvM_NVM_EXCLUSIVE_AREA_0()
#define SchM_Exit_NvM_NVM_EXCLUSIVE_AREA_0()
#define SchM_Enter_BswM_BSWM_EXCLUSIVE_AREA_0()
#define SchM_Exit_BswM_BSWM_EXCLUSIVE_AREA_0()

#endif /* SCHM_H */
