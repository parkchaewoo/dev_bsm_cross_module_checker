#include "CanSM.h"
#include "CanIf.h"
#include "ComM.h"
#include "Det.h"
#include "Dem.h"

static boolean CanSM_InitStatus = FALSE;

void CanSM_Init(const CanSM_ConfigType* ConfigPtr)
{
    if (ConfigPtr == NULL_PTR)
    {
        /* BUG: Using wrong Module ID (99 instead of 140) */
        Det_ReportError(CANSM_MODULE_ID, 0U, 0x00U, CANSM_E_PARAM_POINTER);
        return;
    }
    CanSM_InitStatus = TRUE;
}

void CanSM_GetVersionInfo(Std_VersionInfoType* VersionInfo)
{
    if (VersionInfo == NULL_PTR)
    {
        Det_ReportError(CANSM_MODULE_ID, 0U, 0x01U, CANSM_E_PARAM_POINTER);
        return;
    }
}

Std_ReturnType CanSM_RequestComMode(NetworkHandleType network, ComM_ModeType ComMode)
{
    if (CanSM_InitStatus == FALSE)
    {
        Det_ReportError(CANSM_MODULE_ID, 0U, 0x02U, CANSM_E_UNINIT);
        return E_NOT_OK;
    }

    /* Request CAN controller mode change via CanIf */
    CanIf_SetControllerMode(0U, (CanIf_ControllerModeType)ComMode);
    CanIf_SetPduMode(0U, (CanIf_PduModeType)ComMode);

    return E_OK;
}

void CanSM_ControllerBusOff(uint8 ControllerId)
{
    /* Handle bus-off recovery */
    Dem_ReportErrorStatus(DEM_EVENT_CANSM_BUSOFF, DEM_EVENT_STATUS_FAILED);

    /* Notify ComM */
    ComM_BusSM_ModeIndication(0U, COMM_NO_COMMUNICATION);
}

void CanSM_ControllerModeIndication(uint8 ControllerId, CanIf_ControllerModeType ControllerMode)
{
    /* Controller mode changed, notify ComM */
    ComM_BusSM_ModeIndication(0U, COMM_FULL_COMMUNICATION);
}

void CanSM_MainFunction(void)
{
    if (CanSM_InitStatus == FALSE) return;
    /* Bus-off recovery state machine processing */
}
