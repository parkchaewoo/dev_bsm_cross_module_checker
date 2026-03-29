#ifndef CANIF_CFG_H
#define CANIF_CFG_H

/* CanIf PDU IDs */
#define CanIfConf_CanIfTxPduCfg_Msg1_Tx    0x00U
#define CanIfConf_CanIfTxPduCfg_Msg2_Tx    0x01U
#define CanIfConf_CanIfRxPduCfg_Msg1_Rx    0x10U
#define CanIfConf_CanIfRxPduCfg_Msg2_Rx    0x11U

#define CANIF_DEV_ERROR_DETECT    STD_ON

/* DLC */
#define CanIf_Msg1_Tx_DLC    8U
#define CanIf_Msg2_Tx_DLC    8U

#endif /* CANIF_CFG_H */
