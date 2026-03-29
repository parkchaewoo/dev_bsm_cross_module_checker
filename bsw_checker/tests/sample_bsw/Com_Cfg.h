#ifndef COM_CFG_H
#define COM_CFG_H

/* COM Configuration */
#define COM_DEV_ERROR_DETECT    STD_ON

/* Symbolic Name PDU IDs */
#define ComConf_ComIPdu_Msg1_Tx    0x00U
#define ComConf_ComIPdu_Msg2_Tx    0x01U
#define ComConf_ComIPdu_Msg1_Rx    0x10U
#define ComConf_ComIPdu_Msg2_Rx    0x11U

/* Signal IDs */
#define ComConf_ComSignal_Sig_Speed       0x00U
#define ComConf_ComSignal_Sig_EngineRPM   0x01U
#define ComConf_ComSignal_Sig_Temperature 0x02U

/* PDU Lengths */
#define Com_Msg1_Tx_DLC    8U
#define Com_Msg2_Tx_DLC    8U

#endif /* COM_CFG_H */
