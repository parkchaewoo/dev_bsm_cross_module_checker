#include "Det.h"

static boolean Det_InitStatus = FALSE;

void Det_Init(void)
{
    Det_InitStatus = TRUE;
}

Std_ReturnType Det_ReportError(uint16 ModuleId, uint8 InstanceId, uint8 ApiId, uint8 ErrorId)
{
    /* Log error to debug buffer / breakpoint */
    return E_OK;
}

Std_ReturnType Det_ReportRuntimeError(uint16 ModuleId, uint8 InstanceId, uint8 ApiId, uint8 ErrorId)
{
    return E_OK;
}

void Det_Start(void)
{
    /* Start DET error logging */
}
