#ifndef DET_H
#define DET_H

#include "Std_Types.h"

#define DET_MODULE_ID    15U

extern void Det_Init(void);
extern Std_ReturnType Det_ReportError(uint16 ModuleId, uint8 InstanceId, uint8 ApiId, uint8 ErrorId);
extern Std_ReturnType Det_ReportRuntimeError(uint16 ModuleId, uint8 InstanceId, uint8 ApiId, uint8 ErrorId);
extern void Det_Start(void);

#endif /* DET_H */
