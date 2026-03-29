#include "ComM.h"
#include "CanSM.h"
#include "Nm.h"
#include "Det.h"
#include "BswM.h"

static boolean ComM_InitStatus = FALSE;

void ComM_Init(const ComM_ConfigType* ConfigPtr)
{
    if (ConfigPtr == NULL_PTR)
    {
        Det_ReportError(COMM_MODULE_ID, 0U, 0x01U, COMM_E_WRONG_PARAMETERS);
        return;
    }
    ComM_InitStatus = TRUE;
}

void ComM_DeInit(void)
{
    ComM_InitStatus = FALSE;
}

Std_ReturnType ComM_RequestComMode(ComM_UserHandleType User, ComM_ModeType ComMode)
{
    if (ComM_InitStatus == FALSE)
    {
        Det_ReportError(COMM_MODULE_ID, 0U, 0x05U, COMM_E_UNINIT);
        return E_NOT_OK;
    }

    /* Request mode from bus-specific SM */
    CanSM_RequestComMode(0U, ComMode);

    /* Notify BswM of mode request */
    BswM_ComM_CurrentMode(0U, ComMode);

    return E_OK;
}

Std_ReturnType ComM_GetCurrentComMode(ComM_UserHandleType User, ComM_ModeType* ComModePtr)
{
    if (ComModePtr == NULL_PTR)
    {
        Det_ReportError(COMM_MODULE_ID, 0U, 0x08U, COMM_E_WRONG_PARAMETERS);
        return E_NOT_OK;
    }
    *ComModePtr = COMM_FULL_COMMUNICATION;
    return E_OK;
}

void ComM_BusSM_ModeIndication(NetworkHandleType Channel, ComM_ModeType ComMode)
{
    /* Received mode indication from CanSM/LinSM */
    BswM_ComM_CurrentMode(Channel, ComMode);
}

void ComM_CommunicationAllowed(NetworkHandleType Channel, boolean Allowed)
{
    /* EcuM signals that communication is allowed/not allowed */
}

void ComM_MainFunction(void)
{
    if (ComM_InitStatus == FALSE) return;
    /* Communication inhibition, mode management */
}
