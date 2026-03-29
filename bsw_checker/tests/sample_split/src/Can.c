#include "Can.h"
#include "CanIf.h"
#include "Det.h"
#include "Dem.h"

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

void Can_GetVersionInfo(Std_VersionInfoType* versioninfo)
{
    if (versioninfo == NULL_PTR)
    {
        Det_ReportError(CAN_MODULE_ID, 0U, 0x07U, CAN_E_PARAM_POINTER);
        return;
    }
}

Can_ReturnType Can_Write(Can_HwHandleType Hth, const Can_PduType* PduInfo)
{
    if (Can_InitStatus == FALSE)
    {
        Det_ReportError(CAN_MODULE_ID, 0U, 0x06U, CAN_E_UNINIT);
        return CAN_NOT_OK;
    }
    if (PduInfo == NULL_PTR)
    {
        Det_ReportError(CAN_MODULE_ID, 0U, 0x06U, CAN_E_PARAM_POINTER);
        return CAN_NOT_OK;
    }
    if (PduInfo->length > 64U)
    {
        Det_ReportError(CAN_MODULE_ID, 0U, 0x06U, CAN_E_PARAM_DLC);
        return CAN_NOT_OK;
    }

    /* Write to CAN hardware registers */
    /* ... HW access ... */

    return CAN_OK;
}

Can_ReturnType Can_SetControllerMode(uint8 Controller, Can_StateTransitionType Transition)
{
    if (Can_InitStatus == FALSE)
    {
        Det_ReportError(CAN_MODULE_ID, 0U, 0x03U, CAN_E_UNINIT);
        return CAN_NOT_OK;
    }
    /* Notify CanIf of mode change */
    CanIf_ControllerModeIndication(Controller, (CanIf_ControllerModeType)Transition);
    return CAN_OK;
}

void Can_DisableControllerInterrupts(uint8 Controller)
{
    /* Disable CAN HW interrupts */
}

void Can_EnableControllerInterrupts(uint8 Controller)
{
    /* Enable CAN HW interrupts */
}

void Can_MainFunction_Write(void)
{
    /* Poll Tx completion, call CanIf_TxConfirmation for completed frames */
    CanIf_TxConfirmation(0U);
}

void Can_MainFunction_Read(void)
{
    /* Poll Rx FIFO, call CanIf_RxIndication for received frames */
    Can_HwType mailbox;
    PduInfoType pduInfo;
    uint8 rxData[8] = {0};

    mailbox.id = 0x100U;
    mailbox.hoh = 0U;
    mailbox.ControllerId = 0U;
    pduInfo.SduLength = 8U;
    pduInfo.SduDataPtr = rxData;

    CanIf_RxIndication(&mailbox, &pduInfo);
}

void Can_MainFunction_BusOff(void)
{
    /* Check bus-off status */
    CanIf_ControllerBusOff(0U);
    /* Report DEM event for bus-off */
    Dem_ReportErrorStatus(DEM_EVENT_CAN_BUSOFF, DEM_EVENT_STATUS_FAILED);
}

void Can_MainFunction_Mode(void)
{
    /* Mode transition processing */
}
