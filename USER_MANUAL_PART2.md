## Checker 상세 설명 (Part 2: Checker 6~10)

---

### Checker 6: Init Checker (`init`)

**목적**: EcuM/BswM에서의 BSW 모듈 초기화 순서, Init 함수 호출 여부,
Config 파라미터 전달을 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| INIT-001 | WARN | EcuM/BswM 모듈 자체가 없음 |
| INIT-002 | WARN | 모듈의 Init이 EcuM/BswM에서 호출되지 않음 |
| INIT-003 | FAIL | AUTOSAR 권장 초기화 순서 위반 |
| INIT-004 | WARN | Init 호출 시 NULL config 전달 |
| INIT-005 | WARN | Init 의존 모듈이 스캔 결과에 없음 |

#### 검출 예시 1: 초기화 순서 위반 (INIT-003)

```c
/* EcuM.c - BUG: Com_Init을 PduR_Init보다 먼저 호출 */
void EcuM_Init(void)
{
    Det_Init();
    Can_Init(&Can_Config);

    Com_Init(&Com_Config);   /* WRONG: PduR보다 먼저! */
    PduR_Init(&PduR_Config); /* Com이 이미 초기화된 후 */
    /* 올바른 순서: Can → CanIf → PduR → Com */
}
```
```
[FAIL] [INIT-003] System: Init order violation: Com before PduR
  AUTOSAR recommends initializing PduR first.
  Com depends on PduR for PDU transmission.
  Fix: Move PduR_Init() before Com_Init()

[FAIL] [INIT-003] System: Init order violation: Com before CanIf
  Fix: Move CanIf_Init() before Com_Init()
```

#### 검출 예시 2: Init에 NULL 전달 (INIT-004)

```c
/* EcuM.c */
void EcuM_Init(void)
{
    NvM_Init();           /* NvM_Init(void)이라 문제없지만 */
    Dem_Init();           /* BUG: Dem_ConfigType* 파라미터를 안 넘김 */
    Fee_Init();           /* Fee도 마찬가지 */
}
```
```
[WARN] [INIT-004] Dem: Dem_Init() called with NULL config
  Module Dem expects a valid 'Dem_ConfigType*' pointer.
```

#### 검출 예시 3: Init 미호출 모듈 (INIT-002)

```c
/* EcuM.c - SchM_Init()을 호출하지 않음 */
void EcuM_Init(void)
{
    Det_Init();
    Can_Init(&Can_Config);
    /* SchM_Init(); <-- 누락 */
}
```
```
[WARN] [INIT-002] SchM: SchM_Init() not found in EcuM/BswM
  Module may not be initialized at startup.
  Fix: Add SchM_Init() call to EcuM startup sequence
```

---

### Checker 7: DET Checker (`det`)

**목적**: Det_ReportError 호출의 Module ID, API Service ID, Error ID 정확성,
SID 유일성, Det 설정 여부를 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| DET-001 | WARN | Det_ReportError의 Module ID가 잘못됨 |
| DET-002 | WARN | 알 수 없는 Error ID 사용 |
| DET-003 | WARN | DET 에러 리포팅이 전혀 없는 모듈 |
| DET-004 | FAIL | MODULE_ID define 값이 AUTOSAR 할당값과 불일치 |
| DET-005 | FAIL | DET error define 값이 SWS와 불일치 |
| DET-006 | FAIL | 동일 모듈 내 SID(API Service ID) 값 중복 |
| DET-007 | INFO | 모듈별 SID 정의 수 보고 |
| DET-008 | WARN | Det_ReportError의 API_ID가 호출 함수와 불일치 |

#### 검출 예시 1: Module ID 불일치 (DET-004)

```c
/* CanSM.h */
/* BUG: AUTOSAR는 CanSM에 Module ID 140을 할당하지만 99로 정의 */
#define CANSM_MODULE_ID    99U

/* CanSM.c */
Det_ReportError(CANSM_MODULE_ID, 0U, 0x00U, CANSM_E_PARAM_POINTER);
/* DET 로그에 Module 99로 기록 → 추적 불가 */
```
```
[FAIL] [DET-004] CanSM: Module ID mismatch: 99 != 140
  CANSM_MODULE_ID is defined as 99 but AUTOSAR assigns 140.
  Wrong Module ID causes incorrect DET error attribution.
```

#### 검출 예시 2: SID 중복 (DET-006)

```c
/* Com.h */
#define COM_SID_INIT           0x01U
#define COM_SID_DEINIT         0x02U
#define COM_SID_SEND_SIGNAL    0x02U  /* BUG: DEINIT과 동일한 0x02! */
```
```
[FAIL] [DET-006] Com: Duplicate SID value 0x02U:
  COM_SID_DEINIT, COM_SID_SEND_SIGNAL
  DET log cannot distinguish which API triggered the error.
```

#### 검출 예시 3: 잘못된 함수에서 잘못된 SID 사용 (DET-008)

```c
/* Com.c */
uint8 Com_ReceiveSignal(Com_SignalIdType SignalId, void* SignalDataPtr)
{
    if (Com_InitStatus == FALSE)
    {
        /* BUG: COM_SID_SEND_SIGNAL을 써야 하는데 COM_SID_INIT 사용 */
        Det_ReportError(COM_MODULE_ID, 0U, COM_SID_INIT, COM_E_UNINIT);
    }
}
```
```
[WARN] [DET-008] Com: SID mismatch: COM_SID_INIT in Com_ReceiveSignal()
  Expected SID for Com_ReceiveSignal, but using COM_SID_INIT.
```

---

### Checker 8: Function Pointer Checker (`fptr`)

**목적**: PduR/CanIf 등의 함수 포인터 라우팅 테이블을 분석하여,
참조된 함수의 존재 여부와 크로스 모듈 연결 관계를 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| FPTR-001 | INFO | 라우팅 테이블의 엔트리 수 보고 |
| FPTR-002 | FAIL | 라우팅 테이블이 존재하지 않는 함수 참조 |
| FPTR-003 | INFO | 콜백 함수 포인터 할당 기록 |
| FPTR-004 | WARN | 라우팅 테이블의 NULL 비율이 50% 초과 |
| FPTR-005 | INFO | 함수 포인터 기반 크로스 모듈 링크 |
| FPTR-006 | INFO | 함수 포인터 호출 그래프 요약 |

#### 검출 예시 1: 존재하지 않는 함수 참조 (FPTR-002)

```c
/* PduR.c */
static const PduR_IfTransmitFpType PduR_TxRoutingTable[] = {
    CanIf_Transmit,              /* OK - 존재함 */
    CanIf_Transmit,              /* OK */
    SoAd_IfTransmit_NotExist,   /* BUG: 이 함수는 어디에도 없음! */
};
```
```
[FAIL] [FPTR-002] PduR: Routing target SoAd_IfTransmit_NotExist() not found
  Function pointer in table 'PduR_TxRoutingTable' references
  SoAd_IfTransmit_NotExist() but this function is not defined.
  This will cause a linker error or runtime crash.
```

#### 검출 예시 2: NULL 비율 과다 (FPTR-004)

```c
/* PduR_PBcfg.c */
static const PduR_IfRxRoutingFpType PduR_RxTable[] = {
    Com_RxIndication,  /* 유효 */
    NULL_PTR,          /* 빈 슬롯 */
    NULL_PTR,          /* 빈 슬롯 */
    NULL_PTR,          /* 빈 슬롯 */
    NULL_PTR,          /* 빈 슬롯 - 5개 중 4개가 NULL = 80% */
};
```
```
[WARN] [FPTR-004] PduR: High NULL ratio in routing table: 4/5
  80% of function pointer entries are NULL.
  Many NULL entries indicate incomplete configuration.
```

---

### Checker 9: SchM Checker (`schm`)

**목적**: SchM_Enter/SchM_Exit Exclusive Area 호출의 쌍 검증,
매크로 정의 존재, 네이밍 컨벤션, 크로스 모듈 EA 사용을 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| SCHM-001 | FAIL | SchM_Enter 후 대응하는 SchM_Exit 없음 (또는 반대) |
| SCHM-002 | WARN | Enter/Exit 호출 수 불일치 |
| SCHM-003 | WARN | EA 매크로가 SchM.h에 정의되지 않음 |
| SCHM-004 | INFO | EA 이름이 AUTOSAR 표준 패턴 아님 |
| SCHM-005 | WARN | 다른 모듈의 Exclusive Area 사용 |

#### 검출 예시 1: Enter 후 Exit 없음 (SCHM-001)

```c
/* Com.c - BUG: Enter만 있고 Exit 없음 → 영구 인터럽트 잠김 */
uint8 Com_SendSignal(Com_SignalIdType SignalId, const void* data)
{
    SchM_Enter_Com_COM_EXCLUSIVE_AREA_0();

    /* 시그널 패킹 처리 */
    if (SignalId >= MAX_SIGNALS)
    {
        return COM_E_PARAM;  /* BUG: Exit 없이 return! */
    }

    /* ... 정상 처리 ... */
    SchM_Exit_Com_COM_EXCLUSIVE_AREA_0();
    return E_OK;
}
```
```
[WARN] [SCHM-002] Com: Enter/Exit count mismatch:
  SchM_Com_COM_EXCLUSIVE_AREA_0 (2 Enter vs 1 Exit)
  Mismatched counts may indicate a missing Exit on an error return path.
```

#### 검출 예시 2: 다른 모듈의 EA 사용 (SCHM-005)

```c
/* PduR.c - BUG: Com의 Exclusive Area를 직접 사용 */
Std_ReturnType PduR_ComTransmit(PduIdType id, const PduInfoType* info)
{
    SchM_Enter_Com_COM_EXCLUSIVE_AREA_0();  /* Com의 EA를 PduR가 사용! */
    /* ... */
    SchM_Exit_Com_COM_EXCLUSIVE_AREA_0();
}
/* 올바른 방법: PduR 자체 EA 사용 또는 Com API를 통해 접근 */
```
```
[WARN] [SCHM-005] PduR: PduR uses Com's exclusive area COM_EXCLUSIVE_AREA_0
  Using another module's exclusive area breaks encapsulation.
  Fix: Use PduR's own exclusive area or use Com's public API
```

---

### Checker 10: DEM Event Checker (`dem_event`)

**목적**: 모듈 전체에서 DEM 이벤트 ID(DEM_EVENT_*)의 정의, 사용, 일관성을 추적합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| DEM_EVT-001 | FAIL | 정의되지 않은 DEM 이벤트 ID 사용 |
| DEM_EVT-002 | WARN | 매직 넘버(숫자 리터럴) 이벤트 ID 사용 |
| DEM_EVT-003 | FAIL | 서로 다른 이벤트 이름이 같은 값 사용 |
| DEM_EVT-004 | WARN | 정의되었지만 아무 모듈에서도 사용하지 않는 이벤트 |
| DEM_EVT-005 | INFO | 이벤트를 여러 모듈에서 리포트 (정보) |

#### 검출 예시 1: 정의되지 않은 이벤트 (DEM_EVT-001)

```c
/* Can.c */
void Can_MainFunction_BusOff(void)
{
    /* BUG: DEM_EVENT_CAN_TIMEOUT은 어디에도 정의되지 않음 */
    Dem_ReportErrorStatus(DEM_EVENT_CAN_TIMEOUT, DEM_EVENT_STATUS_FAILED);
}
```
```
[FAIL] [DEM_EVT-001] Can: Undefined DEM event: DEM_EVENT_CAN_TIMEOUT
  Not defined as #define DEM_EVENT_* in any scanned file.
  This will cause a compilation error.
  Fix: Add DEM_EVENT_CAN_TIMEOUT definition to Dem_Cfg.h
```

#### 검출 예시 2: 미사용 이벤트 (DEM_EVT-004)

```c
/* Dem.h */
#define DEM_EVENT_CAN_BUSOFF     0x0001U
#define DEM_EVENT_CANSM_BUSOFF   0x0002U
#define DEM_EVENT_NVM_INTEGRITY  0x0003U
#define DEM_EVENT_ECU_OVERTEMP   0x0004U  /* 정의만 있고 아무도 안 씀 */
```
```
[WARN] [DEM_EVT-004] Dem: Unused DEM event: DEM_EVENT_ECU_OVERTEMP
  Defined in Dem.h but no module calls Dem_SetEventStatus() or
  Dem_ReportErrorStatus() with this ID. Dead configuration.
```

#### 검출 예시 3: 이벤트 ID 값 충돌 (DEM_EVT-003)

```c
/* Dem.h */
#define DEM_EVENT_VOLTAGE_LOW    0x0005U
#define DEM_EVENT_COMM_TIMEOUT   0x0005U  /* 충돌! 같은 값 */
```
```
[FAIL] [DEM_EVT-003] Dem: Duplicate DEM event ID value: 0x0005
  DEM_EVENT_VOLTAGE_LOW and DEM_EVENT_COMM_TIMEOUT share value 0x0005.
  Dem module will confuse different fault conditions.
```
