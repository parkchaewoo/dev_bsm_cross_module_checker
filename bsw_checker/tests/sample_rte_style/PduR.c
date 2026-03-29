/* ============================================================
 * PduR_Lcfg.c - Vector DaVinci 스타일 PduR 라우팅 설정
 * 실제 코드 생성 도구가 만드는 패턴 재현
 * ============================================================ */

#include "PduR.h"
#include "PduR_Lcfg.h"
#include "Com.h"
#include "CanIf.h"
#include "CanTp.h"
#include "Dcm.h"
#include "Det.h"

/* ====== AUTOSAR 컴파일러 추상화 매크로 사용 ====== */
#define FUNC(rettype, memclass)  rettype
#define P2CONST(ptrtype, memclass, ptrclass) const ptrtype *
#define P2VAR(ptrtype, memclass, ptrclass) ptrtype *
#define CONSTP2FUNC(rettype, ptrclass, fctname) rettype (* const fctname)
#define VAR(type, memclass) type
#define CONST(type, memclass) const type

#define PDUR_MODULE_ID    51U
#define PDUR_E_UNINIT     0x01U

/* ====== 함수 포인터 타입 (AUTOSAR 추상화 매크로 사용) ====== */
typedef FUNC(Std_ReturnType, PDUR_CODE) (*PduR_UpIfTransmitFctPtrType)(
    PduIdType txPduId,
    P2CONST(PduInfoType, AUTOMATIC, PDUR_APPL_DATA) pduInfoPtr
);

typedef FUNC(void, PDUR_CODE) (*PduR_UpIfRxIndicationFctPtrType)(
    PduIdType rxPduId,
    P2CONST(PduInfoType, AUTOMATIC, PDUR_APPL_DATA) pduInfoPtr
);

typedef FUNC(void, PDUR_CODE) (*PduR_UpIfTxConfirmationFctPtrType)(
    PduIdType txPduId
);

typedef FUNC(BufReq_ReturnType, PDUR_CODE) (*PduR_UpTpStartOfReceptionFctPtrType)(
    PduIdType pduId,
    P2CONST(PduInfoType, AUTOMATIC, PDUR_APPL_DATA) infoPtr,
    PduLengthType tpSduLength,
    P2VAR(PduLengthType, AUTOMATIC, PDUR_APPL_DATA) bufferSizePtr
);

typedef FUNC(BufReq_ReturnType, PDUR_CODE) (*PduR_UpTpCopyRxDataFctPtrType)(
    PduIdType pduId,
    P2CONST(PduInfoType, AUTOMATIC, PDUR_APPL_DATA) infoPtr,
    P2VAR(PduLengthType, AUTOMATIC, PDUR_APPL_DATA) bufferSizePtr
);

typedef FUNC(void, PDUR_CODE) (*PduR_UpTpRxIndicationFctPtrType)(
    PduIdType pduId,
    Std_ReturnType result
);

/* ====== 라우팅 테이블 구조체 (중첩 구조) ====== */
typedef struct {
    PduR_UpIfRxIndicationFctPtrType   IfRxIndicationFctPtr;
    PduR_UpIfTxConfirmationFctPtrType IfTxConfirmationFctPtr;
} PduR_UpIfLayerFctPtrType;

typedef struct {
    PduR_UpTpStartOfReceptionFctPtrType StartOfReceptionFctPtr;
    PduR_UpTpCopyRxDataFctPtrType       CopyRxDataFctPtr;
    PduR_UpTpRxIndicationFctPtrType     TpRxIndicationFctPtr;
} PduR_UpTpLayerFctPtrType;

typedef struct {
    PduIdType                           SrcPduId;
    PduIdType                           DestPduId;
    PduR_UpIfTransmitFctPtrType         LoIfTransmitFctPtr;
} PduR_RoutingPathIfTxType;

/* ====== 실제 라우팅 테이블 초기화 (코드 생성 도구 출력) ====== */

/* IF 상위→하위 Tx 라우팅 */
CONST(PduR_RoutingPathIfTxType, PDUR_CONST) PduR_IfTxRoutingPaths[] = {
    /* [0] ComConf_ComIPdu_Msg1_Tx -> CanIfConf_CanIfTxPduCfg_Msg1 */
    { 0x00U, 0x00U, CanIf_Transmit },
    /* [1] ComConf_ComIPdu_Msg2_Tx -> CanIfConf_CanIfTxPduCfg_Msg2 */
    { 0x01U, 0x01U, CanIf_Transmit },
    /* [2] ComConf_ComIPdu_Msg3_Tx -> CanIfConf_CanIfTxPduCfg_Msg3 */
    { 0x02U, 0x02U, CanIf_Transmit },
    /* [3] DcmConf_DcmDslProtocolRow_Diag_Tx -> CanTp */
    { 0x10U, 0x10U, NULL_PTR },  /* TP 사용이므로 IF Transmit 없음 */
};

/* IF 하위→상위 Rx 콜백 테이블 */
CONST(PduR_UpIfLayerFctPtrType, PDUR_CONST) PduR_IfRxCallbacks[] = {
    /* [0] -> Com (일반 메시지) */
    { Com_RxIndication, Com_TxConfirmation },
    /* [1] -> Com (일반 메시지) */
    { Com_RxIndication, Com_TxConfirmation },
    /* [2] -> NULL (미설정) */
    { NULL_PTR, NULL_PTR },
};

/* TP 상위 콜백 테이블 */
CONST(PduR_UpTpLayerFctPtrType, PDUR_CONST) PduR_TpRxCallbacks[] = {
    /* [0] -> Dcm (진단 메시지) */
    { Dcm_StartOfReception, Dcm_CopyRxData, Dcm_TpRxIndication },
};

/* ====== AUTOSAR 매크로 사용 함수 구현 ====== */

FUNC(void, PDUR_CODE) PduR_Init(
    P2CONST(PduR_ConfigType, AUTOMATIC, PDUR_PBCFG) ConfigPtr
)
{
    if (ConfigPtr == NULL_PTR)
    {
        Det_ReportError(PDUR_MODULE_ID, 0U, 0x01U, PDUR_E_UNINIT);
        return;
    }
}

FUNC(Std_ReturnType, PDUR_CODE) PduR_ComTransmit(
    VAR(PduIdType, AUTOMATIC) TxPduId,
    P2CONST(PduInfoType, AUTOMATIC, PDUR_APPL_DATA) PduInfoPtr
)
{
    /* 라우팅 테이블에서 함수 포인터로 호출 */
    if (TxPduId < 4U)
    {
        if (PduR_IfTxRoutingPaths[TxPduId].LoIfTransmitFctPtr != NULL_PTR)
        {
            return PduR_IfTxRoutingPaths[TxPduId].LoIfTransmitFctPtr(
                PduR_IfTxRoutingPaths[TxPduId].DestPduId,
                PduInfoPtr
            );
        }
    }
    return E_NOT_OK;
}

FUNC(void, PDUR_CODE) PduR_CanIfRxIndication(
    VAR(PduIdType, AUTOMATIC) RxPduId,
    P2CONST(PduInfoType, AUTOMATIC, PDUR_APPL_DATA) PduInfoPtr
)
{
    /* 함수 포인터 테이블을 통한 간접 호출 */
    if (RxPduId < 3U)
    {
        if (PduR_IfRxCallbacks[RxPduId].IfRxIndicationFctPtr != NULL_PTR)
        {
            PduR_IfRxCallbacks[RxPduId].IfRxIndicationFctPtr(RxPduId, PduInfoPtr);
        }
    }
}

FUNC(void, PDUR_CODE) PduR_CanIfTxConfirmation(
    VAR(PduIdType, AUTOMATIC) TxPduId
)
{
    if (TxPduId < 3U)
    {
        if (PduR_IfRxCallbacks[TxPduId].IfTxConfirmationFctPtr != NULL_PTR)
        {
            PduR_IfRxCallbacks[TxPduId].IfTxConfirmationFctPtr(TxPduId);
        }
    }
}
