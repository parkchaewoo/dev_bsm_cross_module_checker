#include "NvM.h"
#include "Fee.h"
#include "Det.h"
#include "Dem.h"
#include "SchM_NvM.h"

static boolean NvM_InitStatus = FALSE;

void NvM_Init(void)
{
    NvM_InitStatus = TRUE;
}

Std_ReturnType NvM_ReadBlock(NvM_BlockIdType BlockId, void* NvM_DstPtr)
{
    if (NvM_InitStatus == FALSE)
    {
        Det_ReportError(NVM_MODULE_ID, 0U, 0x06U, NVM_E_NOT_INITIALIZED);
        return E_NOT_OK;
    }

    SchM_Enter_NvM_NVM_EXCLUSIVE_AREA_0();
    /* Queue read job, will be processed by Fee in NvM_MainFunction */
    Std_ReturnType ret = Fee_Read(BlockId, 0U, (uint8*)NvM_DstPtr, 64U);
    SchM_Exit_NvM_NVM_EXCLUSIVE_AREA_0();

    return ret;
}

Std_ReturnType NvM_WriteBlock(NvM_BlockIdType BlockId, const void* NvM_SrcPtr)
{
    if (NvM_InitStatus == FALSE)
    {
        Det_ReportError(NVM_MODULE_ID, 0U, 0x07U, NVM_E_NOT_INITIALIZED);
        return E_NOT_OK;
    }

    return Fee_Write(BlockId, (uint8*)NvM_SrcPtr);
}

void NvM_ReadAll(void)
{
    /* Read all configured permanent RAM blocks */
}

void NvM_WriteAll(void)
{
    /* Write all modified RAM blocks */
}

void NvM_MainFunction(void)
{
    if (NvM_InitStatus == FALSE) return;
    /* Process queued read/write jobs */
    /* Check Fee job results */
    /* Report NvM integrity errors to Dem */
    Dem_ReportErrorStatus(DEM_EVENT_NVM_INTEGRITY, DEM_EVENT_STATUS_PASSED);
}
