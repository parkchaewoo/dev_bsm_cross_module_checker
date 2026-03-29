/* ============================================================
 * Com_Rte.c - RTE 통합 Com 모듈 (Rte_Read/Write 패턴)
 * ============================================================ */

#include "Com.h"
#include "Com_Cfg.h"
#include "Rte_Com.h"
#include "PduR_Com.h"
#include "Det.h"
#include "SchM_Com.h"

/* AUTOSAR 컴파일러 추상화 */
#define FUNC(rettype, memclass) rettype
#define P2CONST(ptrtype, memclass, ptrclass) const ptrtype *
#define P2VAR(ptrtype, memclass, ptrclass) ptrtype *
#define VAR(type, memclass) type

#define COM_MODULE_ID    50U
#define COM_E_PARAM      0x01U
#define COM_E_UNINIT     0x02U

/* ====== RTE 콜백 함수 포인터 테이블 ====== */
typedef FUNC(Std_ReturnType, RTE_CODE) (*Rte_CbkFuncPtrType)(void);

/* RTE가 생성하는 Tx/Rx 콜백 테이블 */
CONST(Rte_CbkFuncPtrType, COM_CONST) Com_CbkTxAck_Func[] = {
    Rte_COMCbkTxAck_Sig_VehicleSpeed,   /* Signal Tx 완료 콜백 */
    Rte_COMCbkTxAck_Sig_EngineRPM,
    NULL_PTR,
};

CONST(Rte_CbkFuncPtrType, COM_CONST) Com_CbkRxAck_Func[] = {
    Rte_COMCbk_Sig_BrakePressure,       /* Signal Rx 알림 콜백 */
    Rte_COMCbk_Sig_SteeringAngle,
    Rte_COMCbk_Sig_ThrottlePos,
    NULL_PTR,
};

/* ====== I-PDU 콜백 함수 포인터 (RTE 통합) ====== */
typedef FUNC(void, COM_CODE) (*Com_IpduCalloutFuncPtrType)(
    PduIdType PduId,
    P2CONST(PduInfoType, AUTOMATIC, COM_APPL_DATA) PduInfoPtr
);

CONST(Com_IpduCalloutFuncPtrType, COM_CONST) Com_TxIpduCallout_Func[] = {
    Com_Ipdu_Msg1_Tx_Callout,   /* 각 I-PDU별 Callout 함수 */
    Com_Ipdu_Msg2_Tx_Callout,
    NULL_PTR,
};

/* ====== VAR(static, ...) 패턴 - init 상태 ====== */
static VAR(boolean, COM_VAR) Com_InitStatus = FALSE;

/* ====== 내부 버퍼 (RTE 접근) ====== */
static VAR(uint8, COM_VAR_NOINIT) Com_IpduBuf_Msg1[8];
static VAR(uint8, COM_VAR_NOINIT) Com_IpduBuf_Msg2[8];
static VAR(uint8, COM_VAR_NOINIT) Com_IpduBuf_Msg3[8];

/* I-PDU 버퍼 포인터 배열 */
static P2VAR(uint8, AUTOMATIC, COM_VAR) Com_IpduBufPtrs[] = {
    Com_IpduBuf_Msg1,
    Com_IpduBuf_Msg2,
    Com_IpduBuf_Msg3,
};

/* ====== AUTOSAR FUNC 매크로 사용 API ====== */

FUNC(void, COM_CODE) Com_Init(
    P2CONST(Com_ConfigType, AUTOMATIC, COM_PBCFG) config
)
{
    VAR(uint8, AUTOMATIC) idx;
    if (config == NULL_PTR)
    {
        Det_ReportError(COM_MODULE_ID, 0U, 0x01U, COM_E_PARAM);
        return;
    }
    for (idx = 0U; idx < 3U; idx++)
    {
        uint8 i;
        for (i = 0U; i < 8U; i++)
        {
            Com_IpduBufPtrs[idx][i] = 0U;
        }
    }
    Com_InitStatus = TRUE;
}

FUNC(void, COM_CODE) Com_DeInit(void)
{
    Com_InitStatus = FALSE;
}

FUNC(uint8, COM_CODE) Com_SendSignal(
    VAR(Com_SignalIdType, AUTOMATIC) SignalId,
    P2CONST(void, AUTOMATIC, COM_APPL_DATA) SignalDataPtr
)
{
    VAR(PduInfoType, AUTOMATIC) pduInfo;

    if (Com_InitStatus == FALSE)
    {
        Det_ReportError(COM_MODULE_ID, 0U, 0x0AU, COM_E_UNINIT);
        return 0x80U;
    }

    SchM_Enter_Com_COM_EXCLUSIVE_AREA_0();

    /* 시그널 값을 I-PDU 버퍼에 패킹 */
    /* ... 바이트 오더 변환 등 ... */

    SchM_Exit_Com_COM_EXCLUSIVE_AREA_0();

    /* PduR로 전송 요청 */
    pduInfo.SduLength = 8U;
    pduInfo.SduDataPtr = Com_IpduBufPtrs[0];  /* 실제 버퍼 포인터 */
    PduR_ComTransmit(0U, &pduInfo);

    /* RTE Tx 콜백 호출 */
    if (Com_CbkTxAck_Func[SignalId] != NULL_PTR)
    {
        Com_CbkTxAck_Func[SignalId]();
    }

    return 0U;
}

FUNC(uint8, COM_CODE) Com_ReceiveSignal(
    VAR(Com_SignalIdType, AUTOMATIC) SignalId,
    P2VAR(void, AUTOMATIC, COM_APPL_DATA) SignalDataPtr
)
{
    if (Com_InitStatus == FALSE)
    {
        Det_ReportError(COM_MODULE_ID, 0U, 0x0BU, COM_E_UNINIT);
        return 0x80U;
    }
    return 0U;
}

FUNC(void, COM_CODE) Com_RxIndication(
    VAR(PduIdType, AUTOMATIC) RxPduId,
    P2CONST(PduInfoType, AUTOMATIC, COM_APPL_DATA) PduInfoPtr
)
{
    if (PduInfoPtr == NULL_PTR) return;

    SchM_Enter_Com_COM_EXCLUSIVE_AREA_1();
    /* I-PDU 데이터를 내부 버퍼에 복사 */
    SchM_Exit_Com_COM_EXCLUSIVE_AREA_1();

    /* RTE Rx 콜백 호출 (시그널 변경 알림) */
    if (Com_CbkRxAck_Func[RxPduId] != NULL_PTR)
    {
        Com_CbkRxAck_Func[RxPduId]();
    }
}

FUNC(void, COM_CODE) Com_TxConfirmation(VAR(PduIdType, AUTOMATIC) TxPduId)
{
    /* TxConfirmation 처리 */
}

FUNC(void, COM_CODE) Com_MainFunctionRx(void)
{
    if (Com_InitStatus == FALSE) return;
}

FUNC(void, COM_CODE) Com_MainFunctionTx(void)
{
    if (Com_InitStatus == FALSE) return;
    /* 주기적 전송 처리 */
    VAR(PduInfoType, AUTOMATIC) pduInfo;
    pduInfo.SduLength = 8U;
    pduInfo.SduDataPtr = Com_IpduBufPtrs[0];
    PduR_ComTransmit(0U, &pduInfo);
}
