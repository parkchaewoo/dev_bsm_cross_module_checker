#ifndef NM_H
#define NM_H

#include "Std_Types.h"
#include "ComStack_Types.h"

#define NM_MODULE_ID    29U

typedef uint8 Nm_StateType;
typedef uint8 Nm_ModeType;

extern void Nm_Init(void);
extern Std_ReturnType Nm_NetworkRequest(NetworkHandleType nmNetworkHandle);
extern Std_ReturnType Nm_NetworkRelease(NetworkHandleType nmNetworkHandle);
extern void Nm_MainFunction(void);

#endif /* NM_H */
