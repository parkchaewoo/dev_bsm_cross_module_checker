#include "BswM.h"
#include "Det.h"
#include "ComM.h"
#include "SchM_BswM.h"

static boolean BswM_InitStatus = FALSE;

void BswM_Init(const BswM_ConfigType* ConfigPtr)
{
    if (ConfigPtr == NULL_PTR)
    {
        Det_ReportError(BSWM_MODULE_ID, 0U, 0x00U, BSWM_E_NULL_POINTER);
        return;
    }
    BswM_InitStatus = TRUE;
}

void BswM_DeInit(void)
{
    BswM_InitStatus = FALSE;
}

void BswM_RequestMode(BswM_UserType requesting_user, BswM_ModeType requested_mode)
{
    if (BswM_InitStatus == FALSE)
    {
        Det_ReportError(BSWM_MODULE_ID, 0U, 0x02U, BSWM_E_UNINIT);
        return;
    }
    /* Evaluate mode arbitration rules */
}

void BswM_ComM_CurrentMode(NetworkHandleType Network, ComM_ModeType RequestedMode)
{
    /* ComM mode changed, execute action list */
    if (RequestedMode == COMM_FULL_COMMUNICATION)
    {
        /* Enable COM I-PDU groups */
    }
}

void BswM_MainFunction(void)
{
    if (BswM_InitStatus == FALSE) return;
    SchM_Enter_BswM_BSWM_EXCLUSIVE_AREA_0();
    /* Process deferred mode requests and action lists */
    SchM_Exit_BswM_BSWM_EXCLUSIVE_AREA_0();
}
