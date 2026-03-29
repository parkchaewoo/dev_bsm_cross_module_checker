#ifndef COM_CFG_H
#define COM_CFG_H

#define COM_DEV_ERROR_DETECT    STD_ON
#define COM_VERSION_INFO_API    STD_ON

/* ====== TX PDU IDs (sent from Com to PduR) ====== */
#define ComConf_ComIPdu_Msg1_Tx    0x00U
#define ComConf_ComIPdu_Msg2_Tx    0x01U
#define ComConf_ComIPdu_Msg3_Tx    0x05U   /* BUG: PduR has 0x06 for this! */
#define ComConf_ComIPdu_Msg4_Tx    0x03U
#define ComConf_ComIPdu_Diag_Tx    0x04U

/* ====== RX PDU IDs (received by Com from PduR) ====== */
#define ComConf_ComIPdu_Msg1_Rx    0x10U
#define ComConf_ComIPdu_Msg2_Rx    0x11U
#define ComConf_ComIPdu_Msg3_Rx    0x12U
#define ComConf_ComIPdu_Msg4_Rx    0x13U
#define ComConf_ComIPdu_Diag_Rx    0x14U

/* ====== Signal IDs ====== */
#define ComConf_ComSignal_Sig_VehicleSpeed      0x00U
#define ComConf_ComSignal_Sig_EngineRPM         0x01U
#define ComConf_ComSignal_Sig_EngineTemp        0x02U
#define ComConf_ComSignal_Sig_BrakePressure     0x03U
#define ComConf_ComSignal_Sig_SteeringAngle     0x04U
/* BUG: Signal ID collision! Same ID as Sig_SteeringAngle */
#define ComConf_ComSignal_Sig_ThrottlePos       0x04U
#define ComConf_ComSignal_Sig_GearPosition      0x05U
#define ComConf_ComSignal_Sig_TurnSignal        0x06U
#define ComConf_ComSignal_Sig_Odometer          0x07U
#define ComConf_ComSignal_Sig_FuelLevel         0x08U
#define ComConf_ComSignal_Sig_BatteryVoltage    0x09U

/* ====== PDU Lengths (DLC) ====== */
#define Com_Msg1_Tx_DLC    8U
#define Com_Msg2_Tx_DLC    8U
#define Com_Msg3_Tx_DLC    8U   /* BUG: CanIf says 6 bytes! */
#define Com_Msg4_Tx_DLC    4U
#define Com_Diag_Tx_DLC    64U

/* I-PDU Group configuration */
#define COM_IPDU_GROUP_TX    0U
#define COM_IPDU_GROUP_RX    1U

#define COM_OK                    0x00U
#define COM_BUSY                  0x01U
#define COM_SERVICE_NOT_AVAILABLE 0x80U

#endif /* COM_CFG_H */
