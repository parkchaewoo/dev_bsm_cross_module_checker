#ifndef STD_TYPES_H
#define STD_TYPES_H

typedef unsigned char       uint8;
typedef unsigned short      uint16;
typedef unsigned int        uint32;
typedef unsigned long long  uint64;
typedef signed char         sint8;
typedef signed short        sint16;
typedef signed int          sint32;
typedef signed long long    sint64;
typedef float               float32;
typedef double              float64;
typedef unsigned char       boolean;

#define TRUE    1U
#define FALSE   0U
#define NULL_PTR ((void*)0)

#define STD_ON  1U
#define STD_OFF 0U

typedef uint8 Std_ReturnType;
#define E_OK        0x00U
#define E_NOT_OK    0x01U

typedef struct {
    uint16 vendorID;
    uint16 moduleID;
    uint8  sw_major_version;
    uint8  sw_minor_version;
    uint8  sw_patch_version;
} Std_VersionInfoType;

#endif
