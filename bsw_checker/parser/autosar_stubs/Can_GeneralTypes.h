#ifndef CAN_GENERAL_TYPES_H
#define CAN_GENERAL_TYPES_H

#include "Std_Types.h"
#include "ComStack_Types.h"

typedef uint32 Can_IdType;
typedef uint16 Can_HwHandleType;

typedef struct {
    Can_IdType CanId;
    Can_HwHandleType Hoh;
    uint8 ControllerId;
} Can_HwType;

typedef struct {
    Can_IdType id;
    PduIdType swPduHandle;
    uint8 length;
    uint8* sdu;
} Can_PduType;

typedef uint8 Can_ReturnType;
typedef uint8 Can_StateTransitionType;

#define CAN_OK      0x00U
#define CAN_NOT_OK  0x01U
#define CAN_BUSY    0x02U

#endif
