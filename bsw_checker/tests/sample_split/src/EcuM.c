#include "EcuM.h"
#include "Det.h"
#include "Dem.h"
#include "Os.h"
#include "SchM.h"
#include "Fls.h"
#include "Fee.h"
#include "NvM.h"
#include "Can.h"
#include "CanIf.h"
#include "CanTp.h"
#include "PduR.h"
#include "Com.h"
#include "CanSM.h"
#include "ComM.h"
#include "Dcm.h"
#include "BswM.h"

static const Fls_ConfigType Fls_Config = { 0x00000000U, 0x00100000U };
static const Can_ConfigType Can_Config = { 1U, 4U };
static const CanIf_ConfigType CanIf_Config = { 5U, 5U };
static const CanTp_ConfigType CanTp_Config = { 0U };
static const PduR_ConfigType PduR_Config = { 10U, STD_ON };
static const Com_ConfigType Com_Config = { 5U, 10U };
static const CanSM_ConfigType CanSM_Config = { 1U };
static const ComM_ConfigType ComM_Config = { 1U };
static const Dcm_ConfigType Dcm_Config = { 1U };
static const Dem_ConfigType Dem_Config = { 100U };
static const BswM_ConfigType BswM_Config = { 0U };

void EcuM_Init(void)
{
    /* ===== Phase 1: Basic services ===== */
    Det_Init();
    Dem_PreInit(&Dem_Config);

    /* ===== Phase 2: MCAL drivers ===== */
    Fls_Init(&Fls_Config);

    /* BUG: Init order violation! Com_Init BEFORE PduR_Init and CanIf_Init! */
    /* AUTOSAR requires: Can -> CanIf -> PduR -> Com */
    Com_Init(&Com_Config);     /* WRONG: should be after PduR_Init */
    Can_Init(&Can_Config);

    /* ===== Phase 3: ECU Abstraction ===== */
    CanIf_Init(&CanIf_Config);
    CanTp_Init(&CanTp_Config);
    Fee_Init();

    /* ===== Phase 4: Services ===== */
    NvM_Init();
    Dem_Init();
    BswM_Init(&BswM_Config);

    /* ===== Phase 5: Communication ===== */
    PduR_Init(&PduR_Config);   /* WRONG: should be before Com_Init */
    CanSM_Init(&CanSM_Config);
    ComM_Init(&ComM_Config);

    /* ===== Phase 6: Diagnostics ===== */
    Dcm_Init(&Dcm_Config);

    /* Start NvM ReadAll */
    NvM_ReadAll();
}

void EcuM_StartupTwo(void)
{
    /* Start communication */
    ComM_CommunicationAllowed(0U, TRUE);
}

void EcuM_Shutdown(void)
{
    Com_DeInit();
    ComM_DeInit();
    NvM_WriteAll();
    Dem_Shutdown();
}

void EcuM_MainFunction(void)
{
    /* Wakeup validation, sleep mode management */
}

Std_ReturnType EcuM_GetState(EcuM_StateType* state)
{
    if (state == NULL_PTR)
    {
        Det_ReportError(ECUM_MODULE_ID, 0U, 0x07U, ECUM_E_NULL_POINTER);
        return E_NOT_OK;
    }
    return E_OK;
}

Std_ReturnType EcuM_RequestRUN(EcuM_UserType user)
{
    return E_OK;
}

Std_ReturnType EcuM_ReleaseRUN(EcuM_UserType user)
{
    return E_OK;
}

void EcuM_SetWakeupEvent(EcuM_WakeupSourceType sources)
{
}
