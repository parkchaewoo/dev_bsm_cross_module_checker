#ifndef CAN_H
#define CAN_H

#include "Can_GeneralTypes.h"
#include "ComStack_Types.h"

#define CAN_MODULE_ID    80U

#define CAN_E_PARAM_POINTER     0x01U
#define CAN_E_PARAM_HANDLE      0x02U
#define CAN_E_PARAM_DLC         0x03U
#define CAN_E_PARAM_CONTROLLER  0x04U
#define CAN_E_UNINIT            0x05U
#define CAN_E_TRANSITION        0x06U

typedef uint16 Can_HwHandleType;

typedef struct {
    Can_IdType id;
    Can_HwHandleType hoh;
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

typedef struct {
    uint8 dummy;
} Can_ConfigType;

extern void Can_Init(const Can_ConfigType* Config);
extern Can_ReturnType Can_Write(Can_HwHandleType Hth, const Can_PduType* PduInfo);
extern Can_ReturnType Can_SetControllerMode(uint8 Controller, Can_StateTransitionType Transition);
extern void Can_MainFunction_Write(void);
extern void Can_MainFunction_Read(void);
extern void Can_MainFunction_BusOff(void);
extern void Can_MainFunction_Mode(void);

#endif /* CAN_H */
