#include "Dem.h"
#include "NvM.h"
#include "Det.h"

static boolean Dem_InitStatus = FALSE;

void Dem_PreInit(const Dem_ConfigType* ConfigPtr)
{
    if (ConfigPtr == NULL_PTR)
    {
        Det_ReportError(DEM_MODULE_ID, 0U, 0x01U, DEM_E_PARAM_POINTER);
        return;
    }
    /* Pre-initialize event memory */
}

void Dem_Init(void)
{
    /* Read event data from NvM */
    NvM_ReadBlock(0U, NULL_PTR);
    Dem_InitStatus = TRUE;
}

void Dem_Shutdown(void)
{
    /* Store event data to NvM */
    NvM_WriteBlock(0U, NULL_PTR);
    Dem_InitStatus = FALSE;
}

Std_ReturnType Dem_SetEventStatus(Dem_EventIdType EventId, Dem_EventStatusType EventStatus)
{
    if (Dem_InitStatus == FALSE)
    {
        Det_ReportError(DEM_MODULE_ID, 0U, 0x04U, DEM_E_UNINIT);
        return E_NOT_OK;
    }
    /* Process event status change */
    return E_OK;
}

void Dem_ReportErrorStatus(Dem_EventIdType EventId, Dem_EventStatusType EventStatus)
{
    /* Can be called before Dem_Init (pre-init reporting) */
    Dem_SetEventStatus(EventId, EventStatus);
}

void Dem_MainFunction(void)
{
    if (Dem_InitStatus == FALSE) return;
    /* Process debouncing, aging, event memory management */
}
