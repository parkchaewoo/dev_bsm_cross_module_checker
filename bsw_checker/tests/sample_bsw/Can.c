#include "Can.h"
#include "CanIf.h"
#include "Det.h"

static boolean Can_InitStatus = FALSE;

void Can_Init(const Can_ConfigType* Config)
{
    if (Config == NULL_PTR)
    {
        Det_ReportError(CAN_MODULE_ID, 0U, 0x00U, CAN_E_PARAM_POINTER);
        return;
    }
    Can_InitStatus = TRUE;
}

Can_ReturnType Can_Write(Can_HwHandleType Hth, const Can_PduType* PduInfo)
{
    if (Can_InitStatus == FALSE)
    {
        Det_ReportError(CAN_MODULE_ID, 0U, 0x06U, CAN_E_UNINIT);
        return CAN_NOT_OK;
    }
    /* Write to CAN hardware */
    return CAN_OK;
}

Can_ReturnType Can_SetControllerMode(uint8 Controller, Can_StateTransitionType Transition)
{
    return CAN_OK;
}

void Can_MainFunction_Write(void)
{
    /* Check Tx completion, call CanIf_TxConfirmation */
    CanIf_TxConfirmation(0U);
}

void Can_MainFunction_Read(void)
{
    /* Check Rx, call CanIf_RxIndication */
    Can_HwType mailbox = {0};
    PduInfoType pduInfo = {NULL_PTR, 0U};
    CanIf_RxIndication(&mailbox, &pduInfo);
}

void Can_MainFunction_BusOff(void)
{
    CanIf_ControllerBusOff(0U);
}

void Can_MainFunction_Mode(void)
{
    /* Mode processing */
}
