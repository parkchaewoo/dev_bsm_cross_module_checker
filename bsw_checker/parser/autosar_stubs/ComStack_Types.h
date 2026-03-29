#ifndef COMSTACK_TYPES_H
#define COMSTACK_TYPES_H

#include "Std_Types.h"

typedef uint16 PduIdType;
typedef uint16 PduLengthType;
typedef uint8 NetworkHandleType;
typedef uint8 IcomConfigIdType;

typedef struct {
    uint8* SduDataPtr;
    uint8* MetaDataPtr;
    PduLengthType SduLength;
} PduInfoType;

typedef uint8 BufReq_ReturnType;
#define BUFREQ_OK       0x00U
#define BUFREQ_E_NOT_OK 0x01U
#define BUFREQ_E_BUSY   0x02U
#define BUFREQ_E_OVFL   0x03U

typedef struct {
    uint8 TpDataState;
} RetryInfoType;

typedef uint8 ComM_ModeType;

#endif
