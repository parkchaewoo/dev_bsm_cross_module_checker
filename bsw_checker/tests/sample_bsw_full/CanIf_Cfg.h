#ifndef CANIF_CFG_H
#define CANIF_CFG_H

#define CANIF_DEV_ERROR_DETECT    STD_ON

/* ====== CanIf Tx PDU Config ====== */
#define CanIfConf_CanIfTxPduCfg_Msg1_Tx    0x00U
#define CanIfConf_CanIfTxPduCfg_Msg2_Tx    0x01U
#define CanIfConf_CanIfTxPduCfg_Msg3_Tx    0x02U  /* Note: Sequential in CanIf */
#define CanIfConf_CanIfTxPduCfg_Msg4_Tx    0x03U
#define CanIfConf_CanIfTxPduCfg_Diag_Tx    0x04U

/* ====== CanIf Rx PDU Config ====== */
#define CanIfConf_CanIfRxPduCfg_Msg1_Rx    0x10U
#define CanIfConf_CanIfRxPduCfg_Msg2_Rx    0x11U
#define CanIfConf_CanIfRxPduCfg_Msg3_Rx    0x12U
#define CanIfConf_CanIfRxPduCfg_Msg4_Rx    0x13U
#define CanIfConf_CanIfRxPduCfg_Diag_Rx    0x14U

/* ====== DLC (Data Length Code) ====== */
/* BUG: Msg3 DLC=6 here but Com says 8! */
#define CanIf_Msg1_Tx_DLC    8U
#define CanIf_Msg2_Tx_DLC    8U
#define CanIf_Msg3_Tx_DLC    6U  /* MISMATCH with Com_Msg3_Tx_DLC=8 */
#define CanIf_Msg4_Tx_DLC    4U
#define CanIf_Diag_Tx_DLC    64U

/* CAN ID assignments */
#define CANIF_TX_CANID_MSG1   0x100U
#define CANIF_TX_CANID_MSG2   0x101U
#define CANIF_TX_CANID_MSG3   0x102U
#define CANIF_TX_CANID_MSG4   0x103U
#define CANIF_TX_CANID_DIAG   0x7DFU

#endif /* CANIF_CFG_H */
