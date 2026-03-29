#ifndef PDUR_CFG_H
#define PDUR_CFG_H

#define PDUR_DEV_ERROR_DETECT    STD_ON
#define PDUR_ZERO_COST_OPERATION STD_OFF

/* ====== PduR Source PDU IDs (from upper layers) ====== */
#define PduRConf_PduRSrcPdu_Msg1_Tx    0x00U
#define PduRConf_PduRSrcPdu_Msg2_Tx    0x01U
/* BUG: Com uses 0x05 for Msg3_Tx but PduR uses 0x06! */
#define PduRConf_PduRSrcPdu_Msg3_Tx    0x06U
#define PduRConf_PduRSrcPdu_Msg4_Tx    0x03U
#define PduRConf_PduRSrcPdu_Diag_Tx    0x04U

/* ====== PduR Destination PDU IDs (to lower layers) ====== */
#define PduRConf_PduRDestPdu_Msg1_Tx   0x00U
#define PduRConf_PduRDestPdu_Msg2_Tx   0x01U
#define PduRConf_PduRDestPdu_Msg3_Tx   0x06U
#define PduRConf_PduRDestPdu_Msg4_Tx   0x03U
#define PduRConf_PduRDestPdu_Diag_Tx   0x04U

/* ====== PduR Rx PDU IDs (from lower layers) ====== */
#define PduRConf_PduRSrcPdu_Msg1_Rx    0x10U
#define PduRConf_PduRSrcPdu_Msg2_Rx    0x11U
#define PduRConf_PduRSrcPdu_Msg3_Rx    0x12U
#define PduRConf_PduRSrcPdu_Msg4_Rx    0x13U
#define PduRConf_PduRSrcPdu_Diag_Rx    0x14U

#define PduRConf_PduRDestPdu_Msg1_Rx   0x10U
#define PduRConf_PduRDestPdu_Msg2_Rx   0x11U
#define PduRConf_PduRDestPdu_Msg3_Rx   0x12U
#define PduRConf_PduRDestPdu_Msg4_Rx   0x13U
#define PduRConf_PduRDestPdu_Diag_Rx   0x14U

#endif /* PDUR_CFG_H */
