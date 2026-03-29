#include "Fee.h"
#include "Fls.h"
#include "Det.h"

static boolean Fee_InitStatus = FALSE;

void Fee_Init(void)
{
    Fee_InitStatus = TRUE;
}

Std_ReturnType Fee_Read(uint16 BlockNumber, uint16 BlockOffset, uint8* DataBufferPtr, uint16 Length)
{
    if (Fee_InitStatus == FALSE)
    {
        Det_ReportError(FEE_MODULE_ID, 0U, 0x02U, FEE_E_UNINIT);
        return E_NOT_OK;
    }
    /* Calculate flash address from block number */
    Fls_AddressType addr = (Fls_AddressType)(BlockNumber * 256U + BlockOffset);
    return Fls_Read(addr, DataBufferPtr, (Fls_LengthType)Length);
}

Std_ReturnType Fee_Write(uint16 BlockNumber, uint8* DataBufferPtr)
{
    if (Fee_InitStatus == FALSE)
    {
        Det_ReportError(FEE_MODULE_ID, 0U, 0x03U, FEE_E_UNINIT);
        return E_NOT_OK;
    }
    Fls_AddressType addr = (Fls_AddressType)(BlockNumber * 256U);
    return Fls_Write(addr, DataBufferPtr, 256U);
}

Std_ReturnType Fee_EraseImmediateBlock(uint16 BlockNumber)
{
    Fls_AddressType addr = (Fls_AddressType)(BlockNumber * 256U);
    return Fls_Erase(addr, 256U);
}

void Fee_MainFunction(void)
{
    if (Fee_InitStatus == FALSE) return;
    /* Process pending read/write/erase jobs */
}
