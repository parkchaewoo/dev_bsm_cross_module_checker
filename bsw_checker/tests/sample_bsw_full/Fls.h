#ifndef FLS_H
#define FLS_H

#include "Std_Types.h"

#define FLS_MODULE_ID    92U

#define FLS_E_PARAM_CONFIG  0x01U
#define FLS_E_UNINIT        0x11U

typedef uint32 Fls_AddressType;
typedef uint32 Fls_LengthType;

typedef struct {
    uint32 FlsBaseAddress;
    uint32 FlsTotalSize;
} Fls_ConfigType;

extern void Fls_Init(const Fls_ConfigType* ConfigPtr);
extern Std_ReturnType Fls_Erase(Fls_AddressType TargetAddress, Fls_LengthType Length);
extern Std_ReturnType Fls_Write(Fls_AddressType TargetAddress, const uint8* SourceAddressPtr, Fls_LengthType Length);
extern Std_ReturnType Fls_Read(Fls_AddressType SourceAddress, uint8* TargetAddressPtr, Fls_LengthType Length);
extern void Fls_MainFunction(void);

#endif /* FLS_H */
