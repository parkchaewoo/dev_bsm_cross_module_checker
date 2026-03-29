#include "Fls.h"
#include "Det.h"

static boolean Fls_InitStatus = FALSE;

void Fls_Init(const Fls_ConfigType* ConfigPtr)
{
    if (ConfigPtr == NULL_PTR)
    {
        Det_ReportError(FLS_MODULE_ID, 0U, 0x00U, FLS_E_PARAM_CONFIG);
        return;
    }
    Fls_InitStatus = TRUE;
}

Std_ReturnType Fls_Erase(Fls_AddressType TargetAddress, Fls_LengthType Length)
{
    if (Fls_InitStatus == FALSE)
    {
        Det_ReportError(FLS_MODULE_ID, 0U, 0x01U, FLS_E_UNINIT);
        return E_NOT_OK;
    }
    /* Erase flash sectors */
    return E_OK;
}

Std_ReturnType Fls_Write(Fls_AddressType TargetAddress, const uint8* SourceAddressPtr, Fls_LengthType Length)
{
    if (Fls_InitStatus == FALSE)
    {
        Det_ReportError(FLS_MODULE_ID, 0U, 0x02U, FLS_E_UNINIT);
        return E_NOT_OK;
    }
    /* Write to flash */
    return E_OK;
}

Std_ReturnType Fls_Read(Fls_AddressType SourceAddress, uint8* TargetAddressPtr, Fls_LengthType Length)
{
    if (Fls_InitStatus == FALSE)
    {
        Det_ReportError(FLS_MODULE_ID, 0U, 0x07U, FLS_E_UNINIT);
        return E_NOT_OK;
    }
    /* Read from flash */
    return E_OK;
}

void Fls_MainFunction(void)
{
    if (Fls_InitStatus == FALSE) return;
    /* Process async flash operations */
}
