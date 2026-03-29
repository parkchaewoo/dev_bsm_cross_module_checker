#include "EcuM.h"
#include "Det.h"
#include "Can.h"
#include "CanIf.h"
#include "PduR.h"
#include "Com.h"

static const Can_ConfigType Can_Config;
static const CanIf_ConfigType CanIf_Config;
static const PduR_ConfigType PduR_Config;
static const Com_ConfigType Com_Config;

void EcuM_Init(void)
{
    /* Phase 1: Basic drivers */
    Det_Init();

    /* Phase 2: MCAL */
    Can_Init(&Can_Config);

    /* Phase 3: ECU Abstraction */
    CanIf_Init(&CanIf_Config);

    /* Phase 4: Services & Communication */
    PduR_Init(&PduR_Config);
    Com_Init(&Com_Config);
}

void EcuM_StartupTwo(void)
{
    /* Start communication */
}

void EcuM_MainFunction(void)
{
    /* EcuM periodic processing */
}

void EcuM_Shutdown(void)
{
    Com_DeInit();
}
