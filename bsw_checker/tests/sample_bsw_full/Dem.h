#ifndef DEM_H
#define DEM_H

#include "Dem_Types.h"
#include "Std_Types.h"

#define DEM_MODULE_ID    54U

#define DEM_E_PARAM_CONFIG   0x10U
#define DEM_E_PARAM_POINTER  0x11U
#define DEM_E_PARAM_DATA     0x12U
#define DEM_E_UNINIT         0x20U

typedef uint16 Dem_EventIdType;
typedef uint8 Dem_EventStatusType;
typedef uint8 Dem_DTCFormatType;
typedef uint8 Dem_DTCOriginType;
typedef uint8 Dem_UdsStatusByteType;

#define DEM_EVENT_STATUS_PASSED   0x00U
#define DEM_EVENT_STATUS_FAILED   0x01U

/* Event IDs */
#define DEM_EVENT_CAN_BUSOFF     0x0001U
#define DEM_EVENT_CANSM_BUSOFF   0x0002U
#define DEM_EVENT_NVM_INTEGRITY  0x0003U
#define DEM_EVENT_ECU_OVERTEMP   0x0004U

typedef struct {
    uint16 DemMaxNumberEventEntries;
} Dem_ConfigType;

extern void Dem_PreInit(const Dem_ConfigType* ConfigPtr);
extern void Dem_Init(void);
extern void Dem_Shutdown(void);
extern void Dem_GetVersionInfo(Std_VersionInfoType* versioninfo);
extern Std_ReturnType Dem_SetEventStatus(Dem_EventIdType EventId, Dem_EventStatusType EventStatus);
extern void Dem_ReportErrorStatus(Dem_EventIdType EventId, Dem_EventStatusType EventStatus);
extern void Dem_MainFunction(void);

#endif /* DEM_H */
