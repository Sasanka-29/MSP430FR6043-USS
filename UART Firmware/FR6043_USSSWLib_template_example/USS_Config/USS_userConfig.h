
#ifndef _USERCONFIG_H_
#define _USERCONFIG_H_

//#############################################################################
//
//! \file   ussSwLib_userConfig.h
//!
//! \brief  USS SW Library configuration file
//!         
//
//  Group:          MSP
//  Target Device:  MSP430FR604x
//
//  (C) Copyright 2019, Texas Instruments, Inc.
//#############################################################################
// TI Release: USSLib_02_30_00_03
// Release Date: February 04, 2020
//#############################################################################

//*****************************************************************************
// includes
//*****************************************************************************
#include <msp430.h>
#include <stdint.h>
#include <stdbool.h>
#include "ussSwLib.h"
#include "USS_Lib_HAL.h"
#include "IQmathLib.h"
#include "ussSwLibCalibration.h"

//*****************************************************************************
//! \addtogroup ussSwLib_userConfig
//! @{
//*****************************************************************************

#ifdef __cplusplus

extern "C"
{
#endif

/*******************************************************************************
* The following macros allows user to select tone generation type
* *****************************************************************************/
#define USS_PULSE_MODE_SINGLE_TONE                                  0
#define USS_PULSE_MODE_DUAL_TONE                                    1
#define USS_PULSE_MODE_MULTI_TONE                                   2

/*******************************************************************************
* The following macros allows user to select default
* Absolute time of flight computation option
* To switch between computation option update
* USS_ALG_ABS_TOF_COMPUTATION_MODE macro with the desired computation option
******************************************************************************/
#define USS_ALG_ABS_TOF_COMPUTATION_MODE_LOBE                      0
#define USS_ALG_ABS_TOF_COMPUTATION_MODE_HILBERT                   1
#define USS_ALG_ABS_TOF_COMPUTATION_MODE_LOBE_WIDE                 2
#define USS_ALG_ABS_TOF_COMPUTATION_MODE_HILBERT_WIDE              3


/*******************************************************************************
* The following macros allows user to select default
* DtoF computation option
* To switch between computation option update
* USS_ALG_DTOF_COMPUTATION_MODE macro with the desired computation
* option
******************************************************************************/
#define USS_ALG_DTOF_COMPUTATION_OPTION_WATER                       0
#define USS_ALG_DTOF_COMPUTATION_OPTION_ESTIMATE                    1

 /*******************************************************************************
  * The following macros allows user to select default
  * DToF estimate windowing options
  * To switch between computation option update
  * USS_ALG_DTOF_WINDOWING_MODE macro with the desired computation option
  * when USS_ALG_DTOF_COMPUTATION_MODE = USS_ALG_DTOF_COMPUTATION_OPTION_ESTIMATE
  ******************************************************************************/
  #define USS_ALG_DTOF_EST_WINDOW_OPTION_DISABLED                        0
  #define USS_ALG_DTOF_EST_WINDOW_OPTION_ESTIMATE                        1
  #define USS_ALG_DTOF_EST_WINDOW_OPTION_DYNAMIC                         2
  #define USS_ALG_DTOF_EST_WINDOW_OPTION_STATIC                          3

 /*******************************************************************************
  * The following macros allows user to select default
  * DToF estimate windowing options
  * To switch between computation option update
  * USS_ALG_DTOF_WINDOWING_MODE macro with the desired computation option
  * when USS_ALG_DTOF_COMPUTATION_MODE = USS_ALG_DTOF_COMPUTATION_OPTION_WATER
  ******************************************************************************/
  #define USS_ALG_DTOF_WATER_WINDOW_OPTION_DISABLED                      0
  #define USS_ALG_DTOF_WATER_WINDOW_OPTION_ENABLED                       1

 /*******************************************************************************
  * The following macros allows user to select default
  * volume flow calibration options
  * To switch between computation option update
  * USS_ALG_VFR_CALIB_MODE macro with the desired computation option
  ******************************************************************************/
  #define USS_ALG_VFR_CALIB_OPTION_DISABLED                          0
  #define USS_ALG_VFR_CALIB_OPTION_FLOW                              1
  #define USS_ALG_VFR_CALIB_OPTION_FLOW_TEMPERATURE                  2

 /*******************************************************************************
 * The following macros allows user to select default
 * Volume computation option
 * To switch between computation option update
 * USS_ALG_VOLUME_RATE_COMPUTATION_MODE macro with the desired computation
 * option
 ******************************************************************************/
#define USS_ALG_VOLUME_RATE_COMPUTATION_OPTION_WATER                0
#define USS_ALG_VOLUME_RATE_COMPUTATION_OPTION_GENERIC              1
#define USS_ALG_VOLUME_RATE_COMPUTATION_OPTION_GAS                  USS_ALG_VOLUME_RATE_COMPUTATION_OPTION_GENERIC

//******************************************************************************
// defines
//******************************************************************************

/*******************************************************************************
 * USS PULSE GENERATION CONFIGURATION
 *
 * The following parameters configures the ultrasonic pulse generation
 *
 ******************************************************************************/
#define USS_PULSE_MODE                                     USS_PULSE_MODE_MULTI_TONE


#if (USS_PULSE_MODE == USS_PULSE_MODE_SINGLE_TONE)
#define USS_NUM_OF_EXCITATION_PULSES_F1    22
#define USS_F1_FREQ                        170000
#define USS_PULSE_DUTYPERCENT_F1           50
#define USS_NUM_OF_EXCITATION_PULSES       USS_NUM_OF_EXCITATION_PULSES_F1
#elif defined(__MSP430_HAS_SAPH_A__)
#if (USS_PULSE_MODE == USS_PULSE_MODE_DUAL_TONE)
#define USS_NUM_OF_EXCITATION_PULSES_F1    22
#define USS_F1_FREQ                        170000
#define USS_PULSE_DUTYPERCENT_F1           50
#define USS_NUM_OF_EXCITATION_PULSES_F2    0
#define USS_F2_FREQ                        172000
#define USS_PULSE_DUTYPERCENT_F2           50
#define USS_NUM_OF_EXCITATION_PULSES       (USS_NUM_OF_EXCITATION_PULSES_F1 + USS_NUM_OF_EXCITATION_PULSES_F2)
#elif (USS_PULSE_MODE == USS_PULSE_MODE_MULTI_TONE)
#define USS_F1_FREQ                        185000
#define USS_F2_FREQ                        230000
#define USS_NUM_OF_TRILL_PULSES            11
#define USS_NUM_OF_EXCITATION_PULSES       ((2*(USS_NUM_OF_TRILL_PULSES + USS_NUM_OF_ADDTL_TRILL_PULSES)))
#endif
#endif

 #if (USS_PULSE_MODE == USS_PULSE_MODE_MULTI_TONE)
#define USS_NUM_OF_ADDTL_TRILL_PULSES                               0
#endif

#define USS_ADDTL_BIN_PATTERN_SIZE                                  0
#define USS_NUM_OF_STOP_PULSES                                      0



/*******************************************************************************
 * LIBRARY MEMORY OPTIMIZATION CONFIGURATION
 *
 * The following parameters allows to user to reduce capture buffer size and
 * temporary LEA and FRAM buffers.
 *
 ******************************************************************************/
#if defined(__MSP430_HAS_SAPH_A__)
#define USS_SW_LIB_APP_MAX_CAPTURE_SIZE                             500
#if (USS_PULSE_MODE == USS_PULSE_MODE_MULTI_TONE)
#define USS_NUM_OF_MAX_TRILL_PULSES                                 20
#define USS_NUM_OF_MAX_ADDTL_TRILL_PULSES                           10
#endif
#else
#define USS_SW_LIB_APP_MAX_CAPTURE_SIZE                          330
#endif
#define USS_SW_LIB_APP_MAX_FILTER_LENGTH                            20
#define USS_SW_LIB_APP_MAX_FILTER_OPTIONS                           5
#define USS_SW_LIB_APP_MAX_HILBERT_FILTER_OPTIONS                   2
#define USS_SW_LIB_APP_MAX_HILBERT_FILTER_LENGTH                    12
#if (USS_PULSE_MODE == USS_PULSE_MODE_MULTI_TONE)
#define USS_BINARY_ARRAY_MAX_SIZE                                400
#else
#define USS_BINARY_ARRAY_MAX_SIZE                                200
#endif
/*******************************************************************************
 * LIBRARY CAPTURE ACCUMULATION CONFIGURATION
 *
 * The following parameters allows to enable/disable capture accumulation
 * options. WARNING: Enabling accumulation will increase LEA RAM requirements
 *
 * USS_SW_LIB_ENABLE_ACCUMULATION valid options:
 * -true
 * -false
 *
 * USS_ALG_DTOF_INTERVAL valid options:
 *  -USS_dtof_volume_flow_calculation_interval_1 (default)
 *  -USS_dtof_volume_flow_calculation_interval_2
 *  -USS_dtof_volume_flow_calculation_interval_4
 *  -USS_dtof_volume_flow_calculation_interval_8
 *
 * The following definitions are used to initialize the following library
 * parameter:
 * -USS_Capture_Configuration.isCapAccumulationEnabled
 * -USS_Algorithms_User_Configuration.dtofVolInterval
 ******************************************************************************/
#define USS_SW_LIB_ENABLE_ACCUMULATION                                     false
#if (USS_SW_LIB_ENABLE_ACCUMULATION == false)
#define USS_ALG_DTOF_INTERVAL        USS_dtof_volume_flow_calculation_interval_1
#else
#warning "Update to desired calculation interval"
#define USS_ALG_DTOF_INTERVAL        USS_dtof_volume_flow_calculation_interval_4
#endif

/*******************************************************************************
 * LIBRARY CLOCK DEFINITION
 *
 * IMPORTANT: The following defines only specify MCLK and LFXT frequencies at
 * which the application is configured to run. The library DOES NOT configure
 * MCLK, SMCLK or LFXT.
 *
 * This parameter are also using in the derived parameter section to calculate
 * HSPLL counts and LFXT counts.
 *
 * USS_MCLK_FREQ_IN_HZ valid options:
 * - Valid device specific MCLK frequency options
 *
 * USS_LFXT_FREQ_IN_HZ valid options:
 * - Valid device specific MCLK frequency options
 *
 * USS_SYS_MEASUREMENT_PERIOD (in LFXT cycles) valid range:
 * -min: 655 (20 milliseconds) ~50Hz
 * -max: 65535 (2 seconds) ~0.5Hz
 *
 ******************************************************************************/
#if (USS_PULSE_MODE == USS_PULSE_MODE_MULTI_TONE)
#define USS_MCLK_FREQ_IN_HZ                                         16000000
#else
#define USS_MCLK_FREQ_IN_HZ                                         8000000
#endif
#define USS_SMCLK_FREQ_IN_HZ                                        8000000
#define USS_LFXT_FREQ_IN_HZ                                         32768
#define USS_SYS_MEASUREMENT_PERIOD                                  (USS_LFXT_FREQ_IN_HZ / 40u)


// 50Hz output data rate = 20ms period = 655 LFXT cycles (32768 * 0.020)
// #define USS_SYS_MEASUREMENT_PERIOD                                  820

/*******************************************************************************
 * LIBRARY DIAGNOSTIC CONFIGURATION
 *
 * The following configuration allows the application to obtain additional debug
 * message codes during the application process.
 *
 * USS_DIAGNOSTIC_MODE valid options:
 * - USS_diagnostics_mode_2 (default)
 * - USS_diagnostics_mode_0
 *
 ******************************************************************************/
#define USS_DIAGNOSTIC_MODE                               USS_diagnostics_mode_2

/*******************************************************************************
 * LIBRARY METER CONFIGURATION
 *
 * The following configuration allows the application to configure meter
 * specific parameter
 *
 * USS_ACOUSTIC_LENGTH (Acoustic length in us at room temperature)
 * USS_VOLUME_SCALE_FACTOR (Volume Flow Rate Scale Factor)
 * USS_VFR_LARGE_PIPE_ADDL_SF (Volume Flow Rate Additional Scale Factor)
 *
 *
 ******************************************************************************/
#define USS_ACOUSTIC_LENGTH                                             70
#define USS_VOLUME_SCALE_FACTOR                                         85
// The following #define must be set to 1.0f or larger
#define USS_VFR_LARGE_PIPE_ADDL_SF                                      1.000000f
// The following #define must be :
// Set to false if USS_VFR_LARGE_PIPE_ADDL_SF == 1.0f
// Set to true if USS_VFR_LARGE_PIPE_ADDL_SF > 1.0f)
#define USS_VFR_LARGE_PIPE_ADDL_SF_ENABLE                               false

/*******************************************************************************
 * LIBRARY BASIC ULTRASONIC FIRING/CAPTURE CONFIGURATION
 *
 * The library basic configuration section has been split in the following
 * sections:
 *
 * -USS FREQUENCY CONFIGURATION PARAMETERS
 * -USS CAPTURE SEQUENCE CONFIGURATION
 * -USS PULSE GENERATION CONFIGURATION
 * -USS CALIBRATION CONFIGURATION
 *
 ******************************************************************************/
/*******************************************************************************
 * USS FREQUENCY CONFIGURATION PARAMETERS
 *
 * USS_HSPLL_FREQ_IN_MHZ valid parameters:
 * - 80 (default), 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 69, 68
 *
 * USS_HSPLL_INPUT_CLK_TYPE valid parameters:
 * - USS_HSPLL_input_clock_type_ceramic_resonator (default)
 * - USS_HSPLL_input_clock_type_crystal
 *
 * USS_OVER_SAMPLE_RATE valid parameters:
 * -10
 * -20 (default)
 * -40
 * -80
 * -160
 *
 * USS_PLL_XTAL_IN_MHZ valid parameters:
 * -USS_HSPLL_input_clock_freq_8_MHz
 * -USS_HSPLL_input_clock_freq_4_MHz
 *
 * USS_OUTPUT_PLL_XTAL valid parameters:
 * -false (default)
 * -true
 *
 ******************************************************************************/
#define USS_HSPLL_FREQ_IN_MHZ                                              80
// #define USS_HSPLL_INPUT_CLK_TYPE                                           USS_HSPLL_input_clock_type_ceramic_resonator
#define USS_HSPLL_INPUT_CLK_TYPE                                           USS_HSPLL_input_clock_type_crystal
#define USS_SDHS_OVER_SAMPLE_RATE                                          80
#define USS_PLL_XTAL_IN_MHZ                                                USS_HSPLL_input_clock_freq_8_MHz
#define USS_OUTPUT_PLL_XTAL                                                false
#define USS_HSPLL_TOLERANCE_PERCENT                                        0.5

/*******************************************************************************
 * USS CAPTURE SEQUENCE CONFIGURATION
 *
 * USS_SEQUENCE_SELECTION valid parameters:
 * - USS_CAPTURE_SEQUENCE_SELECTION_CH0
 * - USS_CAPTURE_SEQUENCE_SELECTION_CH1
 * - USS_CAPTURE_SEQUENCE_SELECTION_CH0_CH0
 * - USS_CAPTURE_SEQUENCE_SELECTION_CH0_CH1 (default)
 * - USS_CAPTURE_SEQUENCE_SELECTION_CH1_CH0
 * - USS_CAPTURE_SEQUENCE_SELECTION_CH1_CH1
 *
 * USS_CAPTURE_DURATION_USEC vaild range:
 * -min: 1 usec
 * -max: Varies depending on USS_SW_LIB_APP_MAX_CAPTURE_SIZE,
 *       USS_SDHS_OVER_SAMPLE_RATE and USS_HSPLL_FREQ_IN_MHZ
 *
 * For further details regarding min and max values for the following parameter
 * please refer the USS Library API Guide.
 * USS_GAIN_RANGE
 * USS_START_CAPTURE_SEC
 * USS_ADC_SAMP_COUNT_SEC
 * USS_RESTART_CAP_COUNT_SEC
 *
 ******************************************************************************/
#define USS_SEQUENCE_SELECTION                                         USS_CAPTURE_SEQUENCE_SELECTION_CH0_CH1
#define USS_CAPTURE_DURATION_USEC                                      300
#define USS_GAIN_RANGE                                                 USS_Capture_Gain_Range_7_7
#define USS_START_CAPTURE_SEC                                          2.0E-4
#define USS_ADC_SAMP_COUNT_SEC                                         3.7E-4
#define USS_RESTART_CAP_COUNT_SEC                                      4.0E-3

#if(USSSWLIB_ENABLE_EXTERNAL_CIRCUITRY_CONTROL == true)
#define USS_MEASUREMENT_TURN_ON_EXTERNAL_AMP_SEC          1.0E-5
#define USS_MEASUREMENT_ASQTRIGGER_DELAY_SEC              100e-6f
#endif



/*******************************************************************************
 * USS CALIBRATION CONFIGURATION
 *
 * The following parameters configures the ultrasonic:
 * -Automatic Gain Calibration Constant
 *
 * For further details regarding the following parameter please refer the USS
 * Library API Guide.
 * USS_AGC_CONSTANT
 * USS_ALG_CALIBRATED_UPS_DC_OFFSET
 * USS_ALG_CALIBRATED_DNS_DC_OFFSET
 *
 ******************************************************************************/
#define USS_AGC_CONSTANT                                                      60
#define USS_ALG_CALIBRATED_UPS_DC_OFFSET                                       0
#define USS_ALG_CALIBRATED_DNS_DC_OFFSET                                       0


/*******************************************************************************
 * LIBRARY BASIC ALGORITHM CONFIGURATION
 ******************************************************************************/

#define USS_ALG_ABS_TOF_COMPUTATION_MODE            USS_ALG_ABS_TOF_COMPUTATION_MODE_HILBERT_WIDE
#define USS_ALG_DTOF_COMPUTATION_MODE               USS_ALG_DTOF_COMPUTATION_OPTION_ESTIMATE
#define USS_ALG_VOLUME_RATE_COMPUTATION_MODE        USS_ALG_VOLUME_RATE_COMPUTATION_OPTION_GAS


#define USS_ALG_ABS_TOF_INTERVAL                      1
#if (USS_ALG_DTOF_COMPUTATION_MODE == USS_ALG_DTOF_COMPUTATION_OPTION_WATER)
#define USS_ALG_DTOF_WINDOWING_MODE                  USS_ALG_DTOF_WATER_WINDOW_OPTION_DISABLED
#elif (USS_ALG_DTOF_COMPUTATION_MODE == USS_ALG_DTOF_COMPUTATION_OPTION_ESTIMATE)
#define USS_ALG_DTOF_WINDOWING_MODE                  USS_ALG_DTOF_EST_WINDOW_OPTION_DISABLED
#endif
#define USS_ALG_FILT_IS_FILTER_ENABLED                false
#define USS_ENABLE_ABSTOF_LOBE_OFFSET_CORRECTION      false
#define USS_ALG_VFR_CALIB_MODE                        USS_ALG_VFR_CALIB_OPTION_DISABLED
#define USS_ALG_ENABLE_ESTIMATE_TEMPERATURE           false
#define USS_ALG_ADC_ADDITIONAL_CAP_DLY                0.0
#define USS_ALG_DCOFFSET                              0
#define USS_ALG_CLOCK_RELATIVERROR                    _IQ27(0.0)
#define USS_ALG_ABS_TOF_HILB_USE_CUSTOM_COEFF         false

#if(USS_ALG_DTOF_WINDOWING_MODE != USS_ALG_DTOF_EST_WINDOW_OPTION_DISABLED)
#define USS_ALG_WIN_START_INDEX_BACK_OFF_NUM_CYCLES   2
#define USS_ALG_WIN_TRAP_RAMP_NUM_CYCLES              4
#define USS_ALG_WIN_NUM_CYCLES_DELTA                  3
#define USS_ALG_WIN_PEAK_INDEX_2_EDGES_NUM_CYLES      0
#define USS_ALG_WIN_NUM_CYCLES                        (USS_NUM_OF_EXCITATION_PULSES + \
                                                       USS_ALG_WIN_NUM_CYCLES_DELTA)
#endif
/*******************************************************************************
 * LIBRARY ADVANCED ALGORITHM CONFIGURATION
 * For more information regarding the following parameter please refer to the
 * USS API Library Guide
 ******************************************************************************/
#if (USS_ALG_ABS_TOF_COMPUTATION_MODE == USS_ALG_ABS_TOF_COMPUTATION_MODE_LOBE)

#define USS_ALG_RATIO_OF_TRACK_LOBE                         0.5
#define USS_ALG_NUM_PULS_BEFORE_THRSH                       1
#define USS_ALG_SEARCH_LOBE_SAMP                            1
#define USS_ALG_MAX_RATIO_PEAK_2_PEAK_VAR                   0.2
#define USS_ALG_CORR_VAL_THRSH_CHK_FACT                     0.05
#define USS_ALG_SIGN_VAL_THRSH_CHK                          100
#elif (USS_ALG_ABS_TOF_COMPUTATION_MODE == USS_ALG_ABS_TOF_COMPUTATION_MODE_HILBERT)
#define USS_ALG_ABS_TOF_SEARCH_RANGE                        20
#define USS_ALG_ABS_TOF_POS_SEARCH_RANGE                    USS_ALG_ABS_TOF_SEARCH_RANGE
#define USS_ALG_ABS_TOF_NEG_SEARCH_RANGE                    -(USS_NUM_OF_EXCITATION_PULSES + USS_ALG_ABS_TOF_SEARCH_RANGE)
#define USS_ALG_ABS_TOF_HILB_CROSS_THRESHOLD                50.0
#define USS_ALG_CORR_VAL_THRSH_CHK_FACT                     0.05
#define USS_ALG_SIGN_VAL_THRSH_CHK                          100
#elif (USS_ALG_ABS_TOF_COMPUTATION_MODE == USS_ALG_ABS_TOF_COMPUTATION_MODE_LOBE_WIDE)
#define USS_ALG_ABS_TOF_SEARCH_RANGE                        20
#define USS_ALG_ABS_TOF_POS_SEARCH_RANGE                    USS_ALG_ABS_TOF_SEARCH_RANGE
#define USS_ALG_ABS_TOF_NEG_SEARCH_RANGE                    -(USS_NUM_OF_EXCITATION_PULSES + USS_ALG_ABS_TOF_SEARCH_RANGE)
#define USS_ALG_RATIO_OF_TRACK_LOBE                         0.5
#elif (USS_ALG_ABS_TOF_COMPUTATION_MODE == USS_ALG_ABS_TOF_COMPUTATION_MODE_HILBERT_WIDE)
#define USS_ALG_ABS_TOF_HILB_CROSS_THRESHOLD                50.0
#define USS_ALG_ABS_TOF_SEARCH_RANGE                        20
#define USS_ALG_ABS_TOF_POS_SEARCH_RANGE                    USS_ALG_ABS_TOF_SEARCH_RANGE
#define USS_ALG_ABS_TOF_NEG_SEARCH_RANGE                    -(USS_NUM_OF_EXCITATION_PULSES + USS_ALG_ABS_TOF_SEARCH_RANGE)
#else
#error "Invalid Absolute ToF Algorithm Option"
#endif


#if (USS_ALG_DTOF_COMPUTATION_MODE == USS_ALG_DTOF_COMPUTATION_OPTION_WATER)
#define USS_ALG_NUM_CYCLES_SEARCH_CORR            2
#define USS_ALG_HIGH_FLOW_OPTION                  (USS_highFlow_option_disabled)
#define USS_ALG_CYCLESLIPTHRESHOLD                1.1
#define USS_ALG_THRESHOLDX1X3                     2000000
#elif (USS_ALG_DTOF_COMPUTATION_MODE == USS_ALG_DTOF_COMPUTATION_OPTION_ESTIMATE)
#define USS_ALG_MAX_SAMPLE_SHIFT                  40
#define USS_ALG_THRESHOLDX1X3                     2000000
#else
#error "Invalid Delta ToF Algorithm Option"
#endif


/*******************************************************************************
* LIBRARY ALGORITHM BAND-PASS AND HILBERT COEFFICIENT
******************************************************************************/

#define USS_SW_LIB_APP_FILTER_COEFFICIENTS                         \
    {                                                              \
        /*  USS_filterCoeffs_3400000Hz   */                        \
        {    0xFEEA, 0xFFDA, 0xF4E6, 0xFBA5,                       \
             0xFFBB, 0x03BC, 0x155D, 0xDE0E,                       \
             0xF5A0, 0x2E9C, 0xF5A0, 0xDE0E,                       \
             0x155D, 0x03BC, 0xFFBB, 0xFBA5,                       \
             0xF4E6, 0xFFDA, 0xFEEA, 0x0000                        \
        },                                                         \
        /*  USS_filterCoeffs_3600000Hz   */                        \
        {    0x002B, 0xFF01, 0xF563, 0x050D,                       \
             0xFE4C, 0x0F1B, 0x0FDC, 0xE05C,                       \
             0xFAC9, 0x302A, 0xFAC9, 0xE05C,                       \
             0x0FDC, 0x0F1B, 0xFE4C, 0x050D,                       \
             0xF563, 0xFF01, 0x002B, 0x0000                        \
        },                                                         \
        /*  USS_filterCoeffs_3800000Hz   */                        \
        {    0x0120, 0xFAD8, 0xFA10, 0x06E7,                       \
             0xFE1E, 0x14A0, 0x0848, 0xE00B,                       \
             0xFE43, 0x2DAF, 0xFE43, 0xE00B,                       \
             0x0848, 0x14A0, 0xFE1E, 0x06E7,                       \
             0xFA10, 0xFAD8, 0x0120, 0x0000                        \
        },                                                         \
        /*  USS_filterCoeffs_4000000Hz   */                        \
        {    0x0000, 0xF68E, 0x0000, 0x037C,                       \
             0x0000, 0x1714, 0x0000, 0xE229,                       \
             0x0000, 0x2D64, 0x0000, 0xE229,                       \
             0x0000, 0x1714, 0x0000, 0x037C,                       \
             0x0000, 0xF68E, 0x0000, 0x0000                        \
        },                                                         \
        /*  USS_filterCoeffs_Custom   */                           \
        {0},                                                       \
    };

#define USS_SW_LIB_APP_HILB_FILTER_COEFFICIENTS                    \
    {                                                              \
        /*  Predefined Hilbert transform coefficients   */         \
        {  0xFD84, 0x0000, 0xF11F, 0x0000,                         \
           0xB38F, 0x0000, 0x4C71, 0x0000,                         \
           0x0EE1, 0x0000, 0x027C, 0x0000                          \
        },                                                         \
        /*  USS Hilbert Coeffs Custom   */                         \
        {0},                                                       \
    };

/*******************************************************************************
 * LIBRARY ADVANCED ULTRASONIC FIRING/CAPTURE CONFIGURATION
 *
 * For more information regarding the following parameter please refer to the
 * USS API Library Guide
 ******************************************************************************/
#define USS_EOF_SEQUENCE_SELECTION USS_measurement_end_of_sequence_state_power_off
#define USS_CH0_DRIVE_STRENGHT     USS_measurement_drive_strength_pre_trimmed_drive
#define USS_CH1_DRIVE_STRENGHT     USS_measurement_drive_strength_pre_trimmed_drive
#define USS_PAUSE_STATE                          USS_measurement_pause_state_low
#define USS_PULSE_POLARITY         USS_measurement_pulse_polarity_excitation_starts_on_high_pulse
#define USS_PGA_IN_BIAS_COUNT_SEC                                      2.0E-4
#define USS_TURN_ON_ADC_COUNT_SEC                                      2.0E-5
#define USS_TIME_OUT_COUNT_SEC                                         3000e-6
// #define USS_HSPLL_USSXTAL_SETTLING_USEC                                120
#define USS_HSPLL_USSXTAL_SETTLING_USEC                                5000
#define USS_ENABLE_UUPSPREQIGINTERRUPT                                     false
#define USS_ENABLE_SAPH_PING_TRANSMIT                                      false
#define USS_ENABLE_WINDOW_HI_COMP                                          false
#define USS_ENABLE_WINDOW_LO_COMP                                          false
#define USS_WINDOW_HIGH_THRESHOLD                                         (1040)
#define USS_WINDOW_LOW_THRESHOLD                                         (-1040)
#define USS_TRIGGER_CONFIG              USS_Triger_Configuration_Software_Trigger
#define USS_ULP_BIAS_DELAY              USS_measurement_ULP_bias_delay_no_delay
#define USS_BIAS_IMPEDANCE              USS_measurement_bias_impedance_2800_Ohms
#define USS_MUX_CHARGE_PUMP_MODE        USS_measurement_mux_charge_pump_always_off

/******************************************************************************
* LIBRARY DERIVED PARAMETER SECTION
*
* The following section performs additional library configuration based on the
* parameter selection above.
*
* It is highly recommended to not modify the following sections
*
******************************************************************************/
#if (USS_PULSE_MODE == USS_PULSE_MODE_SINGLE_TONE)
#define USS_NUM_OF_EXCITATION_PULSES       USS_NUM_OF_EXCITATION_PULSES_F1
#elif defined(__MSP430_HAS_SAPH_A__)
#if (USS_PULSE_MODE == USS_PULSE_MODE_DUAL_TONE)
#define USS_NUM_OF_EXCITATION_PULSES       (USS_NUM_OF_EXCITATION_PULSES_F1 + USS_NUM_OF_EXCITATION_PULSES_F2)
#elif (USS_PULSE_MODE == USS_PULSE_MODE_MULTI_TONE)
#define USS_NUM_OF_EXCITATION_PULSES       ((2*(USS_NUM_OF_TRILL_PULSES + USS_NUM_OF_ADDTL_TRILL_PULSES)))
#endif
#endif


#if (USS_ALG_ABS_TOF_COMPUTATION_MODE == USS_ALG_ABS_TOF_COMPUTATION_MODE_LOBE)
#define USS_ALG_ABS_TOF_COMPUTATION (USS_Alg_AbsToF_Calculation_Option_lobe)
#elif (USS_ALG_ABS_TOF_COMPUTATION_MODE == USS_ALG_ABS_TOF_COMPUTATION_MODE_HILBERT)
#define USS_ALG_ABS_TOF_COMPUTATION (USS_Alg_AbsToF_Calculation_Option_hilbert)
#elif (USS_ALG_ABS_TOF_COMPUTATION_MODE == USS_ALG_ABS_TOF_COMPUTATION_MODE_LOBE_WIDE)
#define USS_ALG_ABS_TOF_COMPUTATION (USS_Alg_AbsToF_Calculation_Option_lobeWide)
#elif (USS_ALG_ABS_TOF_COMPUTATION_MODE == USS_ALG_ABS_TOF_COMPUTATION_MODE_HILBERT_WIDE)
#define USS_ALG_ABS_TOF_COMPUTATION ( \
        USS_Alg_AbsToF_Calculation_Option_hilbertWide)
#else
#error "Invalid Abs ToF computation option"
#endif


#if (USS_ALG_DTOF_COMPUTATION_MODE == USS_ALG_DTOF_COMPUTATION_OPTION_WATER)
#define USS_ALG_DELTA_TOF_COMPUTATION_OPTION  (USS_Alg_dToF_Calculation_Option_water)
#elif (USS_ALG_DTOF_COMPUTATION_MODE == USS_ALG_DTOF_COMPUTATION_OPTION_ESTIMATE)
#define USS_ALG_DELTA_TOF_COMPUTATION_OPTION  (USS_Alg_dToF_Calculation_Option_estimate)
#else
#error "Invalid Delta ToF computation option"
#endif


#if (USS_ALG_VOLUME_RATE_COMPUTATION_MODE == USS_ALG_VOLUME_RATE_COMPUTATION_OPTION_WATER)
#define USS_ALG_VOLUME_RATE_COMPUTATION_OPTION (USS_Alg_volume_flow_Calculation_Option_water)
#elif (USS_ALG_VOLUME_RATE_COMPUTATION_MODE == USS_ALG_VOLUME_RATE_COMPUTATION_OPTION_GENERIC)
#define USS_ALG_VOLUME_RATE_COMPUTATION_OPTION (USS_Alg_volume_flow_Calculation_Option_generic)
#else
#error "Invalid volume flow rate computation option"
#endif

#define USS_ALG_IS_INIT_ALGORITHMS                          false

#if (USS_PULSE_MODE > 2)
#error \
    "Pulse mode not supported. Please modify USS_PULSE_MODE to a valid configuration."
#endif

#if defined(__MSP430_HAS_SAPH_A__)
#if (USS_NUM_OF_ADDTL_TRILL_PULSES > 0)
#warning \
    "User must provide additional pulse configuration by defining xtraepulse, xtraxpulse, xtraxhper, xtraxlper, xtrahper, xtralper in variables in USS_userConfig.c"
#if (USS_ADDTL_BIN_PATTERN_SIZE == 0)
#error "USS_ADDTL_BIN_PATTERN_SIZE cannot be set to 0 when USS_NUM_OF_ADDTL_TRILL_PULSES > 0"
#endif
#elif (USS_NUM_OF_ADDTL_TRILL_PULSES < 0)
#error "Invalid number of USS_NUM_OF_ADDTL_TRILL_PULSES"
#endif
#endif

#if (USS_HSPLL_FREQ_IN_MHZ == 80)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_80_MHz
#define USS_PLL_FREQ                80e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 79)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_79_MHz
#define USS_PLL_FREQ                79e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 78)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_78_MHz
#define USS_PLL_FREQ                78e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 77)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_77_MHz
#define USS_PLL_FREQ                77e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 76)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_76_MHz
#define USS_PLL_FREQ                76e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 75)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_75_MHz
#define USS_PLL_FREQ                75e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 74)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_74_MHz
#define USS_PLL_FREQ                74e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 73)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_73_MHz
#define USS_PLL_FREQ                73e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 72)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_72_MHz
#define USS_PLL_FREQ                72e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 71)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_71_MHz
#define USS_PLL_FREQ                71e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 70)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_70_MHz
#define USS_PLL_FREQ                70e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 69)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_69_MHz
#define USS_PLL_FREQ                69e6
#elif (USS_HSPLL_FREQ_IN_MHZ == 68)
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_68_MHz
#define USS_PLL_FREQ                68e6
#else
#define    USS_HSPLL_FREQ    USS_HSPLL_output_clk_freq_80_MHz
#define USS_PLL_FREQ                80e6
#endif

#define USS_START_PPG_COUNT        ((USS_PLL_FREQ*USS_START_CAPTURE_SEC)/16)
#define USS_TURN_ON_ADC_COUNT      ((USS_PLL_FREQ*USS_TURN_ON_ADC_COUNT_SEC)/16)
#define USS_PGA_IN_BIAS_COUNT      ((USS_PLL_FREQ*USS_PGA_IN_BIAS_COUNT_SEC)/16)
#define USS_ADC_SAMP_COUNT         ((USS_PLL_FREQ*USS_ADC_SAMP_COUNT_SEC)/16)
#define USS_RESTART_CAP_COUNT      ((USS_PLL_FREQ * USS_RESTART_CAP_COUNT_SEC / \
                                     16) / 16)
#define USS_TIME_OUT_COUNT         ((USS_PLL_FREQ * USS_TIME_OUT_COUNT_SEC / \
                                     4) / 16)
#define USS_LOW_POWER_RESTART_CAP_COUNT (USS_LFXT_FREQ_IN_HZ * \
                                         USS_RESTART_CAP_COUNT_SEC)

#define USS_HSPLL_TEMP         ((USS_PLL_FREQ) / 1600)
#define USS_HSPLL_TEMP2        ((USS_HSPLL_TEMP) * (USS_HSPLL_TOLERANCE_PERCENT))
#define USS_HSPLL_TOLERANCE    (USS_HSPLL_TEMP2*RESONATOR_CALIB_MONITORING_ACLK/(USS_LFXT_FREQ_IN_HZ))

// Macros used to place variables in LEA RAM memory section
#if defined(__TI_COMPILER_VERSION__)
#define _PRAGMA(x) _Pragma (#x)
#define USS_LEA_DATA(var,align) _PRAGMA(DATA_SECTION(var,".leaRAM"))\
        _PRAGMA(DATA_ALIGN(var,(align)))
#elif defined(__IAR_SYSTEMS_ICC__)
#define _PRAGMA(x) _Pragma (#x)
#define USS_LEA_DATA(var,align) _PRAGMA(location="LEARAM")\
        _PRAGMA(data_alignment=align)
#elif defined(__GNUC__)
#define USS_LEA_DATA(var,align) __attribute__((section(".leaRAM")))\
        __attribute__((aligned(align)))
#else
#define USS_LEA_DATA(var,align)
#endif

// This section of the header checks if the application maximum capture size
// is below the supported USS SW library capture size

#if(USS_SW_LIB_ENABLE_ACCUMULATION == true)
#if (USS_SW_LIB_APP_MAX_CAPTURE_SIZE > 372)
#error \
    "USS_SW_LIB_APP_MAX_CAPTURE_SIZE in USS_userConfig.h file must be less than 372"
#else
#define USS_SW_LIB_APP_MAX_ACC_BLOCK  (2 * USS_SW_LIB_APP_MAX_CAPTURE_SIZE)
#endif
#else
#if (USS_SW_LIB_APP_MAX_CAPTURE_SIZE > 620)
#error \
    "USS_SW_LIB_APP_MAX_CAPTURE_SIZE in USS_userConfig.h file must be less than 620"
#else
#define USS_SW_LIB_APP_MAX_ACC_BLOCK                                    0
#endif
#endif

#define ROUND_UP(N, S) ((((N) + (S) - 1) / (S)) * (S))
#define TEMP_SETL     (USS_HSPLL_USSXTAL_SETTLING_USEC * USS_LFXT_FREQ_IN_HZ)
#define USS_HSPLL_USSXTAL_SETTLING_COUNT_TEMP ROUND_UP((TEMP_SETL/100000),10)
#define USS_HSPLL_USSXTAL_SETTLING_COUNT (USS_HSPLL_USSXTAL_SETTLING_COUNT_TEMP \
                                          / 10)

#define DIV_ROUND(N, D) (((N) + ((D)/2)) / (D))

#if(USS_ALG_DTOF_WINDOWING_MODE != USS_ALG_DTOF_EST_WINDOW_OPTION_DISABLED)

#if (USS_ALG_DTOF_COMPUTATION_MODE == USS_ALG_DTOF_COMPUTATION_OPTION_WATER)
#define USS_SW_LIB_APP_MAX_WINDOW_RAMP_SIZE (USS_SW_LIB_APP_MAX_CAPTURE_SIZE + USS_SW_LIB_APP_MAX_FILTER_LENGTH)
#elif (USS_ALG_DTOF_COMPUTATION_MODE == USS_ALG_DTOF_COMPUTATION_OPTION_ESTIMATE)
#define WINDOW_RAMP_TEMP_NUMERATOR (USS_ALG_WIN_TRAP_RAMP_NUM_CYCLES * USS_PLL_FREQ)
#define WINDOW_RAMP_TEMP_DENOMINATOR (USS_F1_FREQ  * USS_SDHS_OVER_SAMPLE_RATE)
#define USS_SW_LIB_APP_MAX_WINDOW_RAMP_TMP DIV_ROUND(WINDOW_RAMP_TEMP_NUMERATOR,WINDOW_RAMP_TEMP_DENOMINATOR)
#define USS_SW_LIB_APP_MAX_WINDOW_RAMP_SIZE ((int)USS_SW_LIB_APP_MAX_WINDOW_RAMP_TMP + 2)
#endif

#endif

#if (USS_ALG_FILT_IS_FILTER_ENABLED == true)
#if (USS_SDHS_OVER_SAMPLE_RATE == 20)
#if (USS_HSPLL_FREQ_IN_MHZ == 80)
#define USS_ALG_FILT_OPTION                                             3
#elif (USS_HSPLL_FREQ_IN_MHZ == 76)
#define USS_ALG_FILT_OPTION                                             2
#elif (USS_HSPLL_FREQ_IN_MHZ == 72)
#define USS_ALG_FILT_OPTION                                             1
#elif (USS_HSPLL_FREQ_IN_MHZ == 68)
#define USS_ALG_FILT_OPTION                                             0
#else
#warning "No predefined band-pass filter is available for the selected USS_OVER_SAMPLE_RATE and USS_HSPLL_FREQ frequency. User is responsible of defining USS_filterCoeffs_Custom entry below"
#define USS_ALG_FILT_OPTION                                             4
#endif
#else
#warning "No predefined band-pass filter is available for the selected USS_OVER_SAMPLE_RATE and USS_HSPLL_FREQ frequency. User is responsible of defining USS_filterCoeffs_Custom entry below"
#define USS_ALG_FILT_OPTION                                             4
#endif
#endif

#if (USS_ALG_ABS_TOF_HILB_USE_CUSTOM_COEFF == false)
#define USS_HILB_ALG_FILT_OPTION                                        0
#else
#warning \
    "Detected custom hilbert coefficient configuration. Please confirm USS_filterCoeffs_Custom has a valid coefficient configuration"
#define USS_HILB_ALG_FILT_OPTION                                        1
#endif

#if (USS_SDHS_OVER_SAMPLE_RATE == 10)
#define USS_OVER_SAMPLE_RATE \
    USS_Capture_Over_Sample_Rate_10
#elif (USS_SDHS_OVER_SAMPLE_RATE == 20)
#define USS_OVER_SAMPLE_RATE \
    USS_Capture_Over_Sample_Rate_20
#elif (USS_SDHS_OVER_SAMPLE_RATE == 40)
#define USS_OVER_SAMPLE_RATE \
    USS_Capture_Over_Sample_Rate_40
#elif (USS_SDHS_OVER_SAMPLE_RATE == 80)
#define USS_OVER_SAMPLE_RATE \
    USS_Capture_Over_Sample_Rate_80
#elif (USS_SDHS_OVER_SAMPLE_RATE == 160)
#define USS_OVER_SAMPLE_RATE \
    USS_Capture_Over_Sample_Rate_160
#else
#error "Invalid USS_SDHS_OVER_SAMPLE_RATE configuration"
#endif

#define USS_USER_CONFIG_NUMBER_OF_SAMPLES_PER_CAPTURE    \
  ((USS_CAPTURE_DURATION_USEC*USS_HSPLL_FREQ_IN_MHZ)/USS_SDHS_OVER_SAMPLE_RATE)

#if (USS_USER_CONFIG_NUMBER_OF_SAMPLES_PER_CAPTURE > \
     USS_SW_LIB_APP_MAX_CAPTURE_SIZE)
#error \
    "USS_USER_CONFIG_NUMBER_OF_SAMPLES_PER_CAPTURE exceeds USS_SW_LIB_APP_MAX_CAPTURE_SIZE"
#endif

#if (USS_PULSE_MODE != USS_PULSE_MODE_SINGLE_TONE)
#ifdef __MSP430_HAS_SAPH__
#error \
    "Dual or Multi-Tone configuration is not supported on MSP430 devices without SAPH_A module"
#endif
#endif

#if (USSSWLIB_ENABLE_EXTERNAL_CIRCUITRY_CONTROL == true)
#define USS_MEASUREMENT_TURN_ON_EXTERNAL_AMP_COUNT  (USS_SMCLK_FREQ_IN_HZ * \
                                                     USS_MEASUREMENT_TURN_ON_EXTERNAL_AMP_SEC)


#define USS_MEASUREMENT_ASQTRIGGER_DELAY_CYCLES       \
                    (USS_MEASUREMENT_ASQTRIGGER_DELAY_SEC*USS_SMCLK_FREQ_IN_HZ)
#endif


#define USS_Alg_dToF_Calculation_Option_water               1
#define USS_Alg_dToF_Calculation_Option_estimate            0
#define USS_highFlow_option_disabled                        0
#define USS_highFlow_option_version1                        1
#define USS_highFlow_option_version2                        2


#if (USS_ALG_DELTA_TOF_COMPUTATION_OPTION == USS_Alg_dToF_Calculation_Option_water)
#if (USS_ALG_HIGH_FLOW_OPTION != USS_highFlow_option_disabled)
#warning "USS_highFlow_option_version1 and USS_highFlow_option_version2 are \
discourage for new development. It is highly recommended to switch to \
USS_ALG_DELTA_TOF_COMPUTATION_OPTION = USS_Alg_dToF_Calculation_Option_estimate.\
When using USS_Alg_dToF_Calculation_Option_estimate, USS_ALG_HIGH_FLOW_OPTION \
is a don't care."
#endif
#endif


//******************************************************************************

//*****************************************************************************
// typedefs
//*****************************************************************************

//*****************************************************************************
// globals
//*****************************************************************************
//! \brief global ultrasonic library configuration
//!
extern USS_SW_Library_configuration gUssSWConfig;
extern USS_Pulse_Single_Dual_Tone_Configuration singDualToneConfig;
extern USS_Pulse_Multitone_Configuration multiToneConfig;
extern USS_Pulse_Additional_End_of_Sequence_Configuration ussEndOfSeq;
//*****************************************************************************
// the function prototypes
//*****************************************************************************

#ifdef __cplusplus
}
#endif // extern "C"
//@}  // ingroup

#endif // end of  _USERCONFIG_H_ definition
