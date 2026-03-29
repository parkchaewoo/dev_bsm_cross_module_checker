#ifndef FEE_H
#define FEE_H

#include "Std_Types.h"

#define FEE_MODULE_ID    21U

#define FEE_E_UNINIT             0x01U
#define FEE_E_INVALID_BLOCK_NO   0x02U

typedef struct {
    uint8 dummy;
} Fee_ConfigType;

extern void Fee_Init(void);
extern Std_ReturnType Fee_Read(uint16 BlockNumber, uint16 BlockOffset, uint8* DataBufferPtr, uint16 Length);
extern Std_ReturnType Fee_Write(uint16 BlockNumber, uint8* DataBufferPtr);
extern Std_ReturnType Fee_EraseImmediateBlock(uint16 BlockNumber);
extern void Fee_MainFunction(void);

#endif /* FEE_H */
