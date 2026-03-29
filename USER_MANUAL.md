# BSW AUTOSAR Spec Checker - User Manual

## 1. Overview

BSW AUTOSAR Spec Checker는 AUTOSAR BSW(Basic Software) 모듈의 C/H 소스 파일을
분석하여 AUTOSAR 스펙 준수 여부와 모듈 간 인터페이스 정합성을 자동 검증하는 도구입니다.

### 주요 특징
- **15개 검증 Checker**: API, 크로스 모듈, PDU/Signal, Init 순서, DET, 버퍼 안전 등
- **4개 AUTOSAR 버전 지원**: 4.0.3, 4.4.0, 4.9.0, 20.0.0
- **모듈별 버전 선택**: 각 모듈에 다른 AUTOSAR 버전 적용 가능
- **GUI + CLI**: macOS Calendar 스타일 GUI 및 커맨드라인 인터페이스

### 사용법

```bash
# CLI 모드
python -m bsw_checker /path/to/bsw --version 4.4.0

# 모듈별 버전 지정
python -m bsw_checker /path/to/bsw --module-version Com:4.4.0,CanIf:4.0.3

# GUI 모드
python -m bsw_checker --gui
```

### Checker 목록 요약

| # | Checker | Rule ID | 설명 |
|---|---------|---------|------|
| 1 | api_checker | API-001~005 | 필수 API 존재 및 시그니처 검증 |
| 2 | include_checker | INC-001~008 | Include guard, 필수 include, 레이어 위반 |
| 3 | type_checker | TYPE-001~004 | AUTOSAR 표준 타입 및 Config 타입 검증 |
| 4 | cross_module_checker | XMOD-001~007 | 크로스 모듈 호출 체인, 콜백 정합성 |
| 5 | pdu_checker | PDU-001~007 | PDU ID/Signal 매핑, DLC 일관성, 미라우팅 PDU |
| 6 | init_checker | INIT-001~007 | 초기화 순서, Config 파라미터, 이중 Init, DeInit 누락 |
| 7 | det_checker | DET-001~008 | DET 에러 리포팅, Module ID, SID |
| 8 | function_pointer_checker | FPTR-001~006 | 함수 포인터 라우팅 테이블 분석 |
| 9 | schm_checker | SCHM-001~005 | SchM Exclusive Area Enter/Exit 쌍 |
| 10 | dem_event_checker | DEM_EVT-001~005 | DEM 이벤트 ID 추적 및 일관성 |
| 11 | buffer_checker | BUF-001~003 | NULL 포인터 전달, 버퍼 안전 |
| 12 | callback_chain_checker | CHAIN-001~002 | 엔드투엔드 Tx/Rx/TP 콜백 체인 |
| 13 | config_checker | CFG-001~005 | Cfg.h, 포스트빌드, DEV_ERROR_DETECT |
| 14 | naming_checker | NAME-001~003 | AUTOSAR 네이밍 컨벤션 |
| 15 | version_compat_checker | COMPAT-001~002 | 모듈 간 AUTOSAR 버전 호환성 |
| 16 | code_quality_checker | QUAL-001~006 | 리턴값 무시, 프로토타입 불일치, 데드코드, 매직넘버 |

---

## 2. Checker 상세 설명

---

### Checker 1: API Checker (`api`)

**목적**: 각 BSW 모듈의 필수 API가 존재하고, 시그니처(리턴 타입, 파라미터 수)가
AUTOSAR SWS와 일치하는지 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| API-001 | FAIL | 필수 API 함수가 존재하지 않음 |
| API-002 | FAIL | API 리턴 타입이 스펙과 불일치 |
| API-003 | FAIL | API 파라미터 수가 스펙과 불일치 |
| API-004 | FAIL | MainFunction이 필요한 모듈에 없음 |
| API-005 | WARN | Init 함수에 Config 파라미터 누락 |

#### 검출 예시 1: 필수 API 누락 (API-001)

```c
/* Com.h - BUG: Com_DeInit()이 선언되지 않음 */
#ifndef COM_H
#define COM_H

void Com_Init(const Com_ConfigType* config);
/* void Com_DeInit(void);  <-- 누락! */
void Com_SendSignal(Com_SignalIdType SignalId, const void* SignalDataPtr);

#endif
```
```
[FAIL] [API-001] Com: Com_DeInit() missing
  Mandatory API Com_DeInit() is required by AUTOSAR 4.4.0 SWS
  Expected: void Com_DeInit()
  Fix: Add Com_DeInit() implementation to Com.c and declaration to Com.h
```

#### 검출 예시 2: 파라미터 수 불일치 (API-003)

```c
/* AUTOSAR 4.4.0에서 Com_TxConfirmation은 2개 파라미터 필요 */
/* BUG: 파라미터 1개만 있음 (4.0.3 시그니처) */
void Com_TxConfirmation(PduIdType TxPduId);

/* 올바른 4.4.0 시그니처: */
/* void Com_TxConfirmation(PduIdType TxPduId, Std_ReturnType result); */
```
```
[FAIL] [API-003] Com: Com_TxConfirmation() wrong parameter count
  Expected: 2 params: PduIdType, Std_ReturnType
  Actual:   1 params: PduIdType TxPduId
  Ref: SWS_Com, API Service ID 0x40
```

#### 검출 예시 3: MainFunction 누락 (API-004)

```c
/* Com.c - BUG: Com_MainFunctionTx가 구현되지 않음 */
void Com_Init(const Com_ConfigType* config) { /* ... */ }
void Com_MainFunctionRx(void) { /* ... */ }
/* void Com_MainFunctionTx(void) -- 누락! 주기적 Tx 처리 불가 */
```
```
[FAIL] [API-004] Com: Com_MainFunctionTx() missing
  Cyclic main function Com_MainFunctionTx() is required but not found.
  Fix: Implement Com_MainFunctionTx() in Com.c and schedule by SchM/OS
```

#### 검출 예시 4: Init에 Config 파라미터 누락 (API-005)

```c
/* EcuM.h - Config 파라미터 없이 Init 선언 */
void EcuM_Init(void);  /* WARN: EcuM_ConfigType* 파라미터가 없음 */

/* 올바른 형태: */
/* void EcuM_Init(const EcuM_ConfigType* ConfigPtr); */
```
```
[WARN] [API-005] EcuM: EcuM_Init() missing config parameter
  Expected: const EcuM_ConfigType*
  Actual:   void
```

---

### Checker 2: Include Checker (`include`)

**목적**: Header 파일의 include guard, 필수 include, 모듈 간 순환 참조,
AUTOSAR 레이어 규칙 위반을 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| INC-001 | FAIL | include guard 누락 |
| INC-002 | WARN | include guard 이름이 비표준 |
| INC-003 | FAIL | #ifndef와 #define 매크로 불일치 |
| INC-004 | FAIL | 필수 include 파일 누락 |
| INC-005 | INFO | 3개 이상 모듈 헤더 참조 (높은 커플링) |
| INC-006 | INFO | 크로스 모듈 헤더 참조 기록 |
| INC-007 | WARN | 모듈 간 순환 include (A↔B) |
| INC-008 | WARN | AUTOSAR 레이어 위반 (하위→상위) |

#### 검출 예시 1: include guard 누락 (INC-001)

```c
/* PduR_Types.h - BUG: include guard 없음 */
typedef uint16 PduR_RoutingPathGroupIdType;
typedef struct {
    uint8 dummy;
} PduR_ConfigType;
/* 여러 파일에서 include하면 redefinition 오류 발생 */
```
```
[FAIL] [INC-001] PduR: Missing include guard in PduR_Types.h
  Fix: Add #ifndef PDUR_TYPES_H / #define PDUR_TYPES_H / #endif
```

#### 검출 예시 2: 순환 include (INC-007)

```c
/* PduR.c */
#include "PduR.h"
#include "Com.h"      /* PduR가 Com 헤더를 include */

/* Com.c */
#include "Com.h"
#include "PduR_Com.h"  /* Com이 PduR 헤더를 include → 순환! */
```
```
[WARN] [INC-007] PduR: Circular include: PduR <-> Com
  Use callback headers (_Cbk.h) for upward references
```

#### 검출 예시 3: AUTOSAR 레이어 위반 (INC-008)

```c
/* Can.c (MCAL 레이어) */
#include "Can.h"
#include "CanIf.h"  /* BUG: MCAL이 상위 레이어(COM) 직접 참조 */
#include "Det.h"    /* BUG: MCAL이 서비스 레이어 직접 참조 */

/* 올바른 방법: CanIf_Cbk.h (콜백 헤더) 사용 */
```
```
[WARN] [INC-008] Can: Layer violation: Can(mcal) includes CanIf(com)
  Lower layer module Can (mcal, level 1) directly includes upper layer
  module CanIf (com, level 3). Use callback headers (CanIf_Cbk.h).
```

---

### Checker 3: Type Checker (`type`)

**목적**: AUTOSAR 표준 타입(Std_ReturnType, PduInfoType 등) 사용 여부와
Config 타입 정의를 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| TYPE-001 | FAIL | 모듈 ConfigType 정의 누락 |
| TYPE-002 | WARN | ConfigType이 struct가 아님 |
| TYPE-003 | WARN | Std_ReturnType 대신 uint8 사용 |
| TYPE-004 | WARN | C 기본 타입 대신 AUTOSAR 타입 사용해야 함 |

#### 검출 예시 1: ConfigType 미정의 (TYPE-001)

```c
/* CanIf.h - BUG: CanIf_ConfigType typedef가 없음 */
#ifndef CANIF_H
#define CANIF_H
void CanIf_Init(const void* ConfigPtr);  /* ConfigType 없이 void* 사용 */
#endif
```
```
[FAIL] [TYPE-001] CanIf: Config type 'CanIf_ConfigType' not found
  Expected: typedef struct { ... } CanIf_ConfigType;
  Fix: Define CanIf_ConfigType in CanIf_Types.h or CanIf_Cfg.h
```

#### 검출 예시 2: C 기본 타입 사용 (TYPE-004)

```c
/* BUG: AUTOSAR에서 'unsigned int'가 아닌 'uint32' 사용해야 함 */
unsigned int Com_GetMessageCount(void);

/* 올바른 형태: */
uint32 Com_GetMessageCount(void);
```
```
[WARN] [TYPE-004] Com: C type 'unsigned int' in Com_GetMessageCount() parameter
  AUTOSAR requires platform-independent types. Use 'uint32'.
```

---

### Checker 4: Cross-Module Checker (`cross`)

**목적**: 모듈 간 함수 호출 체인, 콜백 함수 정의 위치, 선언만 있고 정의 없는
콜백, 콜백 시그니처 정합성을 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| XMOD-001 | FAIL | 스펙에서 기대하는 크로스 모듈 호출이 없음 |
| XMOD-002 | WARN | 콜백 함수가 잘못된 모듈에 정의됨 |
| XMOD-003 | WARN | 함수 포인터가 존재하지 않는 함수 참조 |
| XMOD-004 | FAIL | TX 통신 경로(Com→PduR→CanIf→Can) 불완전 |
| XMOD-005 | FAIL | RX 통신 경로(Can→CanIf→PduR→Com) 불완전 |
| XMOD-006 | FAIL | 헤더에 선언만 있고 .c에 정의 없는 콜백 |
| XMOD-007 | WARN | 콜백 파라미터 타입이 스펙과 불일치 |

#### 검출 예시 1: 크로스 모듈 호출 누락 (XMOD-001)

```c
/* PduR.c - BUG: CanIf_Transmit을 호출하지 않음 */
Std_ReturnType PduR_ComTransmit(PduIdType id, const PduInfoType* info)
{
    /* CanIf_Transmit(id, info); 를 호출해야 하는데 누락 */
    return E_NOT_OK;
}
```
```
[FAIL] [XMOD-001] PduR: PduR does not call CanIf_Transmit()
  This breaks the TX path: PduR_ComTransmit -> CanIf_Transmit
  Fix: Ensure PduR calls CanIf_Transmit() in routing/config tables
```

#### 검출 예시 2: 선언만 있고 정의 없는 콜백 (XMOD-006)

```c
/* CanTp.h - 선언은 있음 */
extern void CanTp_RxIndication(PduIdType RxPduId, const PduInfoType* PduInfoPtr);

/* CanTp.c - BUG: 정의가 없음! */
void CanTp_Init(const CanTp_ConfigType* cfg) { /* ... */ }
void CanTp_Transmit(PduIdType id, const PduInfoType* info) { /* ... */ }
/* CanTp_RxIndication 구현 누락 → CanIf가 호출하면 링커 에러 */
```
```
[FAIL] [XMOD-006] CanTp: CanTp_RxIndication() declared but NOT defined
  Function is declared in CanTp.h but has no definition in any .c file.
  Fix: Implement CanTp_RxIndication() in CanTp.c
```

#### 검출 예시 3: TX 경로 불완전 (XMOD-004)

```
정상 TX 경로: Com → PduR_ComTransmit → CanIf_Transmit → Can_Write

만약 PduR.c에서 CanIf_Transmit을 호출하지 않으면:
```
```
[FAIL] [XMOD-004] System: TX path incomplete
  The CAN transmission path (Com -> PduR -> CanIf -> Can)
  has missing links.
```

---

### Checker 5: PDU Checker (`pdu`)

**목적**: Com, PduR, CanIf 간의 PDU ID 값, Symbolic Name, DLC(Data Length Code),
Signal ID의 일관성을 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| PDU-001 | FAIL | 같은 PDU의 ID 값이 모듈 간 불일치 |
| PDU-002 | PASS/WARN | Symbolic Name 크로스 모듈 매칭 |
| PDU-003 | FAIL | PDU DLC(길이) 모듈 간 불일치 |
| PDU-004 | FAIL | Signal ID 값 충돌 |

#### 검출 예시 1: PDU ID 불일치 (PDU-001)

```c
/* Com_Cfg.h */
#define ComConf_ComIPdu_Msg3_Tx    0x05U   /* Com은 0x05 */

/* PduR_Cfg.h */
#define PduRConf_PduRSrcPdu_Msg3_Tx  0x06U  /* PduR은 0x06 → 불일치! */
```
```
[FAIL] [PDU-001] System: PDU 'Msg3_Tx' ID mismatch across modules
  Values found:
    PduR: PduRConf_PduRSrcPdu_Msg3_Tx = 0x06U
    Com:  ComConf_ComIPdu_Msg3_Tx = 0x05U
  PDU routing failures - sent PDU will not reach destination.
```

#### 검출 예시 2: DLC 불일치 (PDU-003)

```c
/* Com_Cfg.h */
#define Com_Msg3_Tx_DLC    8U    /* Com은 8바이트 */

/* CanIf_Cfg.h */
#define CanIf_Msg3_Tx_DLC  6U   /* CanIf는 6바이트 → 불일치! */
```
```
[FAIL] [PDU-003] System: DLC mismatch for 'Msg3_Tx'
  Com: Com_Msg3_Tx_DLC = 8U
  CanIf: CanIf_Msg3_Tx_DLC = 6U
  DLC mismatch can cause buffer overflows or truncated data.
```

#### 검출 예시 3: Signal ID 충돌 (PDU-004)

```c
/* Com_Cfg.h */
#define ComConf_ComSignal_Sig_SteeringAngle   0x04U
#define ComConf_ComSignal_Sig_ThrottlePos     0x04U  /* 충돌! 같은 ID */
```
```
[FAIL] [PDU-004] System: Signal ID collision:
  ComConf_ComSignal_Sig_ThrottlePos and
  ComConf_ComSignal_Sig_SteeringAngle = 4 (0x0004)
  Same ID causes signal routing confusion at runtime.
```
