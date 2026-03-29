## Checker 상세 설명 (Part 3: Checker 11~16)

---

### Checker 11: Buffer Checker (`buffer`)

**목적**: 모듈 간 함수 호출 시 NULL 포인터 전달, PduInfoType에 NULL SduDataPtr을
설정한 채 Transmit API를 호출하는 위험 패턴을 검출합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| BUF-001 | FAIL | 데이터 버퍼 API에 NULL_PTR 직접 전달 |
| BUF-002 | WARN | SduDataPtr=NULL인 PduInfoType을 Transmit에 전달 |
| BUF-003 | INFO | 필수 API에 Init 가드(초기화 체크) 누락 가능성 |

#### 검출 예시 1: NULL SduDataPtr으로 Transmit (BUF-002)

```c
/* Com.c - BUG: SduDataPtr이 NULL인 채로 전송 요청 */
void Com_MainFunctionTx(void)
{
    PduInfoType pduInfo;
    pduInfo.SduLength = 8U;
    pduInfo.SduDataPtr = NULL_PTR;  /* 실제 데이터 없음! */

    /* PduR에 전달 → PduR이 NULL 포인터 역참조 위험 */
    PduR_ComTransmit(ComConf_ComIPdu_Msg1_Tx, &pduInfo);
}
```
```
[WARN] [BUF-002] Com: PduInfo with NULL SduDataPtr passed to PduR_ComTransmit()
  Variable 'pduInfo' has SduDataPtr=NULL_PTR but is passed to
  PduR_ComTransmit(). The CAN frame will contain garbage data.
  Fix: Set pduInfo.SduDataPtr to point to actual data buffer
```

#### 검출 예시 2: 직접 NULL 전달 (BUF-001)

```c
/* Dem.c */
void Dem_Init(void)
{
    NvM_ReadBlock(0U, NULL_PTR);  /* BUG: 데이터 수신 버퍼가 NULL! */
}
```
```
[FAIL] [BUF-001] Dem: NULL passed to NvM_ReadBlock() param 'NvM_DstPtr'
  Passing NULL will cause null pointer dereference.
  Fix: Provide a valid buffer pointer to NvM_ReadBlock()
```

---

### Checker 12: Callback Chain Checker (`chain`)

**목적**: CAN IF 송수신, TP 분할전송, Bus-off 처리, 모드 제어 등
엔드투엔드 통신 체인의 각 링크가 모두 존재하는지 검증합니다.

#### 검증하는 체인 7가지

| 체인 | 경로 |
|------|------|
| IF-TX | Com → PduR_ComTransmit → CanIf_Transmit → Can_Write |
| IF-RX | Can → CanIf_RxIndication → PduR_CanIfRxIndication → Com_RxIndication |
| IF-TXCONF | Can → CanIf_TxConfirmation → PduR_CanIfTxConfirmation → Com_TxConfirmation |
| TP-RX | CanIf → CanTp_RxIndication → PduR_CanTpStartOfReception → Dcm_StartOfReception |
| TP-TX | Dcm → PduR_DcmTransmit → CanTp_Transmit → CanIf_Transmit |
| BUSOFF | Can → CanIf_ControllerBusOff → CanSM_ControllerBusOff → ComM_BusSM_ModeIndication |
| MODE | ComM → CanSM_RequestComMode → CanIf_SetControllerMode |

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| CHAIN-001 | PASS | 체인의 모든 링크 정상 |
| CHAIN-002 | FAIL | 체인의 특정 링크 누락 |

#### 검출 예시 1: TP-RX 체인 끊김 (CHAIN-002)

```c
/* CanTp.c - BUG: CanTp_RxIndication이 없어서 TP 수신 불가 */
void CanTp_Init(const CanTp_ConfigType* cfg) { /* ... */ }
Std_ReturnType CanTp_Transmit(PduIdType id, const PduInfoType* info) { /* ... */ }
/* CanTp_RxIndication 누락 → 진단 수신 불가! */
```
```
[FAIL] [CHAIN-002] CanTp: Chain TP-RX: CanTp -> PduR_CanTpStartOfReception() missing
  Communication chain 'TP-RX' is broken.
  Purpose: CanTp starts TP reception via PduR.
  Messages sent through this chain will not reach their destination.
```

#### 검출 예시 2: BUSOFF 체인 완전 통과

```c
/* 모든 모듈이 올바르게 구현된 경우 */
/* Can.c:  CanIf_ControllerBusOff(0U);            ✓ */
/* CanIf.c: CanSM_ControllerBusOff(ControllerId); ✓ */
/* CanSM.c: ComM_BusSM_ModeIndication(0U, ...);   ✓ */
```
```
[PASS] [CHAIN-001] System: Chain BUSOFF: all 3 links OK
  Can -> CanIf_ControllerBusOff(): CAN driver reports bus-off
  CanIf -> CanSM_ControllerBusOff(): CanIf notifies CanSM
  CanSM -> ComM_BusSM_ModeIndication(): CanSM notifies ComM
```

---

### Checker 13: Config Checker (`config`)

**목적**: BSW 모듈의 설정 파일 존재, 포스트빌드 구조, DEV_ERROR_DETECT
설정, Config 구조체 내용을 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| CFG-001 | WARN | Module_Cfg.h 파일이 없음 |
| CFG-002 | INFO | 포스트빌드 config 인스턴스 없음 |
| CFG-003 | WARN | ConfigType 구조체에 dummy 멤버만 있음 |
| CFG-004 | INFO/PASS | DEV_ERROR_DETECT 설정 상태 |
| CFG-005 | INFO | GetVersionInfo 있지만 VERSION_INFO_API 없음 |

#### 검출 예시 1: Cfg.h 파일 없음 (CFG-001)

```
프로젝트 디렉토리:
  Com.c, Com.h, Com_Cfg.h     ← OK
  PduR.c, PduR.h, PduR_Cfg.h  ← OK
  Can.c, Can.h                 ← Can_Cfg.h 없음!
```
```
[WARN] [CFG-001] Can: Can_Cfg.h not found
  Module Can should have a Can_Cfg.h configuration header.
  Fix: Generate Can_Cfg.h from AUTOSAR configuration tool
```

#### 검출 예시 2: dummy-only ConfigType (CFG-003)

```c
/* BswM.h */
typedef struct {
    uint8 dummy;  /* 실제 설정 파라미터 없이 더미만 */
} BswM_ConfigType;
```
```
[WARN] [CFG-003] BswM: BswM_ConfigType has only dummy members
  Configuration type contains only dummy/reserved fields.
  A real config struct should contain actual parameters.
  Fix: Regenerate configuration from AUTOSAR tool
```

---

### Checker 14: Naming Checker (`naming`)

**목적**: AUTOSAR 네이밍 컨벤션(<Module>_<Function>, <MODULE>_<MACRO>,
<Module>_<TypeName>) 준수 여부를 검증합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| NAME-001 | WARN | 함수명이 <Module>_ 접두어 없음 |
| NAME-002 | INFO | 매크로명이 <MODULE>_ 접두어 없음 |
| NAME-003 | WARN/INFO | 타입명이 <Module>_ 접두어 없음 |

#### 검출 예시 1: 함수 접두어 없음 (NAME-001)

```c
/* Com.c */
/* BUG: 'ProcessRxPdu'는 Com_ 접두어가 없음 */
void ProcessRxPdu(PduIdType id, const PduInfoType* info)
{
    /* 내부 처리 함수이지만 static이 아니어서 외부 노출 */
}

/* 올바른 형태: */
static void Com_ProcessRxPdu(PduIdType id, const PduInfoType* info);
/* 또는 public이면: */
void Com_ProcessRxPdu(PduIdType id, const PduInfoType* info);
```
```
[WARN] [NAME-001] Com: Function 'ProcessRxPdu' has non-standard prefix
  Expected: Com_<FunctionName>
  AUTOSAR SWS requires public functions to use <Module>_<Name>.
```

#### 검출 예시 2: Config 타입 네이밍 (NAME-003)

```c
/* Com.h */
/* BUG: 'ComConfig'이 아닌 'Com_ConfigType'이어야 함 */
typedef struct {
    uint8 maxPdu;
} ComConfig;
```
```
[WARN] [NAME-003] Com: Config type 'ComConfig' should end with 'ConfigType'
  AUTOSAR convention: <Module>_ConfigType
```

---

### Checker 15: Version Compatibility Checker (`compat`)

**목적**: 모듈별 다른 AUTOSAR 버전을 사용할 때, 서로 상호작용하는 모듈 간
버전 차이로 인한 API 호환성 문제를 검출합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| COMPAT-001 | FAIL/WARN | 상호작용 모듈 간 AUTOSAR 버전 불일치 |
| COMPAT-002 | FAIL | API 시그니처가 설정된 버전과 맞지 않음 |

#### 검출 예시 1: 인접 모듈 버전 불일치 (COMPAT-001)

```bash
# Com은 4.4.0인데 PduR은 4.0.3으로 설정
python -m bsw_checker /path --module-version Com:4.4.0,PduR:4.0.3
```
```
[WARN] [COMPAT-001] System: Version difference: Com(4.4.0) <-> PduR(4.0.3)
  Interacting modules use different AUTOSAR versions.
  Check if API changes between 4.0.3 and 4.4.0 affect the interface.

# 거리가 2 이상이면 FAIL
# 예: Com(4.0.3) <-> PduR(4.9.0) → 거리=2 → FAIL
```
```
[FAIL] [COMPAT-001] System: Version mismatch: Com(4.0.3) <-> PduR(4.9.0)
  API signatures, callback parameters, and behavior may have changed.
  Fix: Align Com and PduR to the same AUTOSAR version
```

#### 검출 예시 2: API가 이전 버전 시그니처 (COMPAT-002)

```c
/* Com.h - 모듈은 4.4.0으로 설정되었지만 API는 4.0.3 시그니처 */
/* 4.0.3: void Com_TxConfirmation(PduIdType TxPduId);           -- 1 param */
/* 4.4.0: void Com_TxConfirmation(PduIdType TxPduId, Std_ReturnType result); -- 2 params */

void Com_TxConfirmation(PduIdType TxPduId);  /* 1 param = 4.0.3 시그니처 */
```
```
[FAIL] [COMPAT-002] Com: Com_TxConfirmation() has 4.0.3 signature
  but module set to 4.4.0
  Expected: 2 params (AUTOSAR 4.4.0)
  Actual:   1 params (AUTOSAR 4.0.3)
  Change: Com_TxConfirmation added Std_ReturnType result parameter
```

---

### Checker 16: Code Quality Checker (`quality`)

**목적**: 리턴값 미처리, .h/.c 프로토타입 불일치, 데드코드, 매직넘버,
SchM+다중 return 위험 패턴을 검출합니다.

#### Rule 목록

| Rule ID | Severity | 설명 |
|---------|----------|------|
| QUAL-001 | WARN | Std_ReturnType 리턴하는 API 호출 후 결과 미확인 |
| QUAL-002 | FAIL | .h 선언과 .c 정의의 리턴 타입 불일치 |
| QUAL-003 | FAIL | .h 선언과 .c 정의의 파라미터 수 불일치 |
| QUAL-004 | INFO | 어디서도 참조되지 않는 함수 (데드코드 의심) |
| QUAL-005 | WARN | 크로스 모듈 API 호출에 매직넘버 사용 |
| QUAL-006 | INFO | SchM_Enter + 다중 return 패턴 (Exit 누락 위험) |

#### 검출 예시 1: 리턴값 무시 (QUAL-001)

```c
/* Com.c - BUG: PduR_ComTransmit 결과를 확인하지 않음 */
void Com_MainFunctionTx(void)
{
    PduInfoType pduInfo;
    pduInfo.SduLength = 8U;

    /* 리턴값 E_OK/E_NOT_OK을 버림! */
    PduR_ComTransmit(ComConf_ComIPdu_Msg1_Tx, &pduInfo);

    /* 올바른 형태: */
    /* if (PduR_ComTransmit(...) != E_OK) { handle error } */
}
```
```
[WARN] [QUAL-001] Com: Return value of PduR_ComTransmit() ignored
  If the call fails (E_NOT_OK), the error goes undetected.
  Fix: if (PduR_ComTransmit(...) != E_OK) { /* handle error */ }
```

#### 검출 예시 2: 프로토타입 불일치 (QUAL-002)

```c
/* Com.h */
Std_ReturnType Com_SendSignal(Com_SignalIdType id, const void* data);

/* Com.c - BUG: 리턴 타입이 다름! */
uint8 Com_SendSignal(Com_SignalIdType id, const void* data)
{
    return 0U;
}
```
```
[FAIL] [QUAL-002] Com: Com_SendSignal() return type mismatch: .h vs .c
  Declared: Std_ReturnType  |  Defined: uint8
  Causes undefined behavior due to calling convention mismatch.
```

#### 검출 예시 3: SchM + 다중 return 위험 (QUAL-006)

```c
/* NvM.c */
Std_ReturnType NvM_ReadBlock(NvM_BlockIdType BlockId, void* dst)
{
    SchM_Enter_NvM_NVM_EXCLUSIVE_AREA_0();

    if (NvM_InitStatus == FALSE)
    {
        Det_ReportError(...);
        return E_NOT_OK;   /* Exit 없이 return → 잠김! */
    }
    if (BlockId >= NVM_MAX_BLOCKS)
    {
        return E_NOT_OK;   /* 여기도 Exit 없이! */
    }

    /* ... 정상 처리 ... */
    SchM_Exit_NvM_NVM_EXCLUSIVE_AREA_0();
    return E_OK;
}
```
```
[INFO] [QUAL-006] NvM: NvM_ReadBlock() has SchM_Enter + 5 returns
  Multiple returns with exclusive area protection is a common
  source of lock-up bugs. Ensure SchM_Exit on all return paths.
```

---

### 추가 확장 Rule (기존 Checker 보강)

#### PDU Checker 추가 Rule

| Rule ID | Severity | 설명 |
|---------|----------|------|
| PDU-005 | WARN | Com PDU가 PduR 라우팅에 없음 (미라우팅) |
| PDU-006 | INFO | PduR PDU가 Com에 없음 (Dcm 등 다른 상위모듈 용) |
| PDU-007 | WARN | PDU 이름에 Tx와 Rx가 동시에 있음 (방향 혼동) |

```c
/* Com_Cfg.h */
#define ComConf_ComIPdu_SpecialMsg_Tx  0x0AU  /* Com에만 있음 */

/* PduR_Cfg.h - SpecialMsg_Tx에 대한 라우팅 없음! */
```
```
[WARN] [PDU-005] System: Com PDU 'SpecialMsg_Tx' not found in PduR routing
  PDU cannot be transmitted because PduR does not know how to route it.
```

#### Init Checker 추가 Rule

| Rule ID | Severity | 설명 |
|---------|----------|------|
| INIT-006 | WARN | 같은 Init 함수가 2번 이상 호출 |
| INIT-007 | INFO | Init만 있고 DeInit/Shutdown 없음 |

```c
/* EcuM.c - BUG: Can_Init 2번 호출 */
void EcuM_Init(void)
{
    Can_Init(&Can_Config);
    CanIf_Init(&CanIf_Config);
    Can_Init(&Can_Config);   /* 실수로 중복! */
}
```
```
[WARN] [INIT-006] Can: Can_Init() called 2 times
  Double initialization can cause loss of runtime state.
  Fix: Remove duplicate Can_Init() call
```

---

## 3. CLI 사용법

### 기본 사용

```bash
# 기본 검증 (FAIL/WARN만 표시)
python -m bsw_checker /path/to/bsw

# PASS 항목도 표시
python -m bsw_checker /path/to/bsw --show-pass

# 모든 항목 표시 (PASS + INFO)
python -m bsw_checker /path/to/bsw --show-pass --show-info
```

### AUTOSAR 버전 설정

```bash
# 전체 모듈에 4.0.3 적용
python -m bsw_checker /path/to/bsw --version 4.0.3

# 모듈별 개별 버전 설정
python -m bsw_checker /path/to/bsw --version 4.4.0 \
  --module-version Com:4.4.0,CanIf:4.0.3,PduR:4.4.0

# --version은 기본값, --module-version에 없는 모듈은 기본값 사용
```

### 모듈/Checker 필터링

```bash
# 특정 모듈만 검증
python -m bsw_checker /path/to/bsw --modules Com,PduR,CanIf

# 특정 Checker만 실행
python -m bsw_checker /path/to/bsw --check api,pdu,chain

# 사용 가능한 Checker 이름:
# api, include, type, cross, pdu, init, det, fptr,
# schm, dem_event, buffer, chain, config, naming, compat
```

### 출력 형식

```bash
# JSON 출력
python -m bsw_checker /path/to/bsw --format json --output report.json

# 콘솔 출력을 파일로
python -m bsw_checker /path/to/bsw --output report.txt
```

### 출력 예시

```
======================================================================
  BSW AUTOSAR Spec Verification Report
======================================================================
  Target:    /home/user/project/bsw
  Default:   AUTOSAR 4.4.0
  Modules:   Can(4.4.0), CanIf(4.0.3), Com(4.4.0), PduR(4.4.0)
  Date:      2026-03-29 12:00:00
======================================================================

--- [FAIL] Com (AUTOSAR 4.4.0) ---
  NG  [API-003] Com_TxConfirmation() wrong parameter count
      Expected: 2 params: PduIdType, Std_ReturnType
      Actual:   1 params: PduIdType TxPduId
      Ref: SWS_Com

  NG  [PDU-001] PDU 'Msg3_Tx' ID mismatch across modules
      Com: 0x05U  /  PduR: 0x06U

--- [PASS] CanIf (AUTOSAR 4.0.3) ---

======================================================================
  Summary: 677 checks | 419 PASS | 24 FAIL | 95 WARN | 139 INFO
======================================================================
```

---

## 4. GUI 사용법

### 실행
```bash
python -m bsw_checker --gui
```

### 화면 구성

```
┌─────────── Sidebar ──────────┬─────────── Content ───────────────┐
│ BSW Checker                  │ Verification Results              │
│ AUTOSAR Spec Verification    │                                   │
│                              │ [Total] [Pass] [Fail] [Warn] [Info]│
│ TARGET PATH                  │                                   │
│ [____________] [...]         │ Filter: (All)(Fail)(Warn)(Pass)   │
│ [Scan & Auto-detect]         │ Module: [All ▼]                   │
│                              │                                   │
│ Default: [4.4.0▼]           │ ┌──────────────────────────────┐  │
│ [All On][All Off][Set All]   │ │Status│Module│Ver │Rule│Desc  │  │
│                              │ │ FAIL │ Com  │4.4 │API │TxCo..│  │
│ MODULE CONFIGURATION         │ │ PASS │CanIf │4.0 │API │Init..│  │
│ Enable Module    AR Ver      │ │ WARN │ PduR │4.4 │INC │Circ..│  │
│ [✓] BswM       [4.4.0▼]    │ └──────────────────────────────┘  │
│ [✓] Can        [4.4.0▼]    │                                   │
│ [✓] CanIf      [4.0.3▼]    │ Detail Panel:                     │
│ [ ] CanTp      [4.4.0▼]    │ [FAIL] [API-003] Com_TxConf...    │
│ [✓] Com        [4.4.0▼]    │ Expected: 2 params                │
│ [✓] EcuM       [4.4.0▼]    │ Location: Com.h:45                │
│ ...                          │ [Confirm] [Reject] [Reset]        │
│                              │                                   │
│ [▓▓▓ Run Verification ▓▓▓]  │ [Export JSON] [Export Text]       │
└──────────────────────────────┴───────────────────────────────────┘
```

### 사용 순서

1. **경로 선택**: "..." 버튼으로 BSW 소스 디렉토리 선택
2. **자동 감지**: "Scan & Auto-detect" 클릭 → 발견된 모듈 자동 체크
3. **버전 설정**: 각 모듈별 AUTOSAR 버전 콤보박스에서 선택
4. **실행**: "Run Verification" 클릭
5. **결과 확인**: 결과 테이블에서 항목 클릭 → 하단 상세 패널
6. **검증**: Confirm(확인) / Reject(거부) 버튼으로 결과 검증
7. **내보내기**: Export JSON / Export Text로 리포트 저장
