#ifndef OS_H
#define OS_H

#include "Std_Types.h"

#define OS_MODULE_ID    1U

extern void Os_Init(void);
extern void Os_GetVersionInfo(Std_VersionInfoType* versioninfo);

#endif /* OS_H */
