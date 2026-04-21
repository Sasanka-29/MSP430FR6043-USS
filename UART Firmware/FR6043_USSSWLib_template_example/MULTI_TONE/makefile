################################################################################
# Automatically-generated file. Do not edit!
################################################################################

SHELL = cmd.exe

CG_TOOL_ROOT := C:/ti/ccs2041/ccs/tools/compiler/ti-cgt-msp430_21.6.1.LTS

GEN_OPTS__FLAG := 
GEN_CMDS__FLAG := 

ORDERED_OBJS += \
"./main.obj" \
"./system_pre_init.obj" \
"./USS_Config/USS_userConfig.obj" \
"./ussSWLib/USS_HAL/USS_Lib_HAL.obj" \
"./ussSWLib/source/common/benchmarkussswLib.obj" \
"./ussSWLib/source/common/ussSwLibCommonHSPLL.obj" \
"./ussSWLib/source/common/ussSwLibCommonInterrupts.obj" \
"./ussSWLib/source/common/ussSwLibCommonSAPH.obj" \
"./ussSWLib/source/common/ussSwLibCommonSDHS.obj" \
"./ussSWLib/source/common/ussSwLibCommonTimer.obj" \
"./ussSWLib/source/common/ussSwLibCommonUSS.obj" \
"./ussSWLib/source/ussSwLibAlgorithm.obj" \
"./ussSWLib/source/ussSwLibAppDebug.obj" \
"./ussSWLib/source/ussSwLibCalibration.obj" \
"./ussSWLib/source/ussSwLibConfiguration.obj" \
"./ussSWLib/source/ussSwLibISR.obj" \
"./ussSWLib/source/ussSwLibMeasurement.obj" \
"./ussSWLib/source/ussSwLibTemperature.obj" \
"./ussSWLib/source/ussSwLibVFRCalib.obj" \
"./ussSWLib/source/ussSwLibVFRCalibFlow.obj" \
"./ussSWLib/source/ussSwLibVFRCalibFlowTemperature.obj" \
"../lnk_msp430fr6043.cmd" \
$(GEN_CMDS__FLAG) \
-llibmpu_init.a \
-llibmath.a \
-l"C:/ti/msp/USS_02_30_00_03/USS/lib/IQMathLibrary/libraries/CCS/MPY32/5xx_6xx/QmathLib.a" \
-l"C:/ti/msp/USS_02_30_00_03/USS/lib/IQMathLibrary/libraries/CCS/MPY32/5xx_6xx/IQmathLib.a" \
-llibc.a \

-include ../makefile.init

RM := DEL /F
RMDIR := RMDIR /S/Q

# All of the sources participating in the build are defined here
-include sources.mk
-include subdir_vars.mk
-include IQMathLib/subdir_vars.mk
-include QMathLib/subdir_vars.mk
-include USS_Config/subdir_vars.mk
-include ussSWLib/USS_HAL/subdir_vars.mk
-include ussSWLib/lib/subdir_vars.mk
-include ussSWLib/source/common/subdir_vars.mk
-include ussSWLib/source/subdir_vars.mk
-include subdir_rules.mk
-include IQMathLib/subdir_rules.mk
-include QMathLib/subdir_rules.mk
-include USS_Config/subdir_rules.mk
-include ussSWLib/USS_HAL/subdir_rules.mk
-include ussSWLib/lib/subdir_rules.mk
-include ussSWLib/source/common/subdir_rules.mk
-include ussSWLib/source/subdir_rules.mk
-include objects.mk

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(C55_DEPS)),)
-include $(C55_DEPS)
endif
ifneq ($(strip $(C_UPPER_DEPS)),)
-include $(C_UPPER_DEPS)
endif
ifneq ($(strip $(S67_DEPS)),)
-include $(S67_DEPS)
endif
ifneq ($(strip $(S62_DEPS)),)
-include $(S62_DEPS)
endif
ifneq ($(strip $(S_DEPS)),)
-include $(S_DEPS)
endif
ifneq ($(strip $(OPT_DEPS)),)
-include $(OPT_DEPS)
endif
ifneq ($(strip $(C??_DEPS)),)
-include $(C??_DEPS)
endif
ifneq ($(strip $(ASM_UPPER_DEPS)),)
-include $(ASM_UPPER_DEPS)
endif
ifneq ($(strip $(S??_DEPS)),)
-include $(S??_DEPS)
endif
ifneq ($(strip $(C64_DEPS)),)
-include $(C64_DEPS)
endif
ifneq ($(strip $(CXX_DEPS)),)
-include $(CXX_DEPS)
endif
ifneq ($(strip $(S64_DEPS)),)
-include $(S64_DEPS)
endif
ifneq ($(strip $(CLA_DEPS)),)
-include $(CLA_DEPS)
endif
ifneq ($(strip $(S55_DEPS)),)
-include $(S55_DEPS)
endif
ifneq ($(strip $(SV7A_DEPS)),)
-include $(SV7A_DEPS)
endif
ifneq ($(strip $(C62_DEPS)),)
-include $(C62_DEPS)
endif
ifneq ($(strip $(C67_DEPS)),)
-include $(C67_DEPS)
endif
ifneq ($(strip $(K_DEPS)),)
-include $(K_DEPS)
endif
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
ifneq ($(strip $(CC_DEPS)),)
-include $(CC_DEPS)
endif
ifneq ($(strip $(C++_DEPS)),)
-include $(C++_DEPS)
endif
ifneq ($(strip $(C43_DEPS)),)
-include $(C43_DEPS)
endif
ifneq ($(strip $(S43_DEPS)),)
-include $(S43_DEPS)
endif
ifneq ($(strip $(ASM_DEPS)),)
-include $(ASM_DEPS)
endif
ifneq ($(strip $(S_UPPER_DEPS)),)
-include $(S_UPPER_DEPS)
endif
ifneq ($(strip $(CPP_DEPS)),)
-include $(CPP_DEPS)
endif
ifneq ($(strip $(SA_DEPS)),)
-include $(SA_DEPS)
endif
endif

-include ../makefile.defs

# Add inputs and outputs from these tool invocations to the build variables 
EXE_OUTPUTS += \
FR6043_USSSWLib_template_example.out 

EXE_OUTPUTS__QUOTED += \
"FR6043_USSSWLib_template_example.out" 


# All Target
all: $(OBJS) $(CMD_SRCS) $(A_SRCS) $(GEN_CMDS)
	@$(MAKE) --no-print-directory -Onone "FR6043_USSSWLib_template_example.out"

# Tool invocations
FR6043_USSSWLib_template_example.out: $(OBJS) $(CMD_SRCS) $(A_SRCS) $(GEN_CMDS)
	@echo 'Building target: "$@"'
	@echo 'Invoking: MSP430 Linker'
	"C:/ti/ccs2041/ccs/tools/compiler/ti-cgt-msp430_21.6.1.LTS/bin/cl430" -vmspx --data_model=large -O3 --use_hw_mpy=F5 --advice:power="none" --advice:hw_config=all --define=__MSP430FR6043__ --define=_MPU_ENABLE --define=__EVM430_ID__=0x43 --define=__EVM430_VER__=0x20 --define=__AFE_EXT_3v3__ --define=USS_PULSE_MODE=2 --printf_support=minimal --diag_warning=225 --diag_wrap=off --display_error_number --large_memory_model --silicon_errata=CPU21 --silicon_errata=CPU22 --silicon_errata=CPU40 -z -m"FR6043_USSSWLib_template_example.map" --heap_size=160 --stack_size=512 --cinit_hold_wdt=on -i"C:/ti/ccs2041/ccs/ccs_base/msp430/include" -i"C:/ti/ccs2041/ccs/ccs_base/msp430/lib/5xx_6xx_FRxx" -i"C:/ti/ccs2041/ccs/ccs_base/msp430/lib/FR59xx" -i"C:/ti/ccs2041/ccs/tools/compiler/ti-cgt-msp430_21.6.1.LTS/lib" -i"C:/ti/ccs2041/ccs/tools/compiler/ti-cgt-msp430_21.6.1.LTS/include" --priority --reread_libs --define=_MPU_ENABLE --diag_wrap=off --display_error_number --warn_sections --xml_link_info="FR6043_USSSWLib_template_example_linkInfo.xml" --use_hw_mpy=F5 --rom_model -o "FR6043_USSSWLib_template_example.out" $(ORDERED_OBJS) $(A_SRCS)
	@echo 'Finished building target: "$@"'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(EXE_OUTPUTS__QUOTED)
	-$(RM) "main.obj" "system_pre_init.obj" "USS_Config\USS_userConfig.obj" "ussSWLib\USS_HAL\USS_Lib_HAL.obj" "ussSWLib\source\common\benchmarkussswLib.obj" "ussSWLib\source\common\ussSwLibCommonHSPLL.obj" "ussSWLib\source\common\ussSwLibCommonInterrupts.obj" "ussSWLib\source\common\ussSwLibCommonSAPH.obj" "ussSWLib\source\common\ussSwLibCommonSDHS.obj" "ussSWLib\source\common\ussSwLibCommonTimer.obj" "ussSWLib\source\common\ussSwLibCommonUSS.obj" "ussSWLib\source\ussSwLibAlgorithm.obj" "ussSWLib\source\ussSwLibAppDebug.obj" "ussSWLib\source\ussSwLibCalibration.obj" "ussSWLib\source\ussSwLibConfiguration.obj" "ussSWLib\source\ussSwLibISR.obj" "ussSWLib\source\ussSwLibMeasurement.obj" "ussSWLib\source\ussSwLibTemperature.obj" "ussSWLib\source\ussSwLibVFRCalib.obj" "ussSWLib\source\ussSwLibVFRCalibFlow.obj" "ussSWLib\source\ussSwLibVFRCalibFlowTemperature.obj" 
	-$(RM) "main.d" "system_pre_init.d" "USS_Config\USS_userConfig.d" "ussSWLib\USS_HAL\USS_Lib_HAL.d" "ussSWLib\source\common\benchmarkussswLib.d" "ussSWLib\source\common\ussSwLibCommonHSPLL.d" "ussSWLib\source\common\ussSwLibCommonInterrupts.d" "ussSWLib\source\common\ussSwLibCommonSAPH.d" "ussSWLib\source\common\ussSwLibCommonSDHS.d" "ussSWLib\source\common\ussSwLibCommonTimer.d" "ussSWLib\source\common\ussSwLibCommonUSS.d" "ussSWLib\source\ussSwLibAlgorithm.d" "ussSWLib\source\ussSwLibAppDebug.d" "ussSWLib\source\ussSwLibCalibration.d" "ussSWLib\source\ussSwLibConfiguration.d" "ussSWLib\source\ussSwLibISR.d" "ussSWLib\source\ussSwLibMeasurement.d" "ussSWLib\source\ussSwLibTemperature.d" "ussSWLib\source\ussSwLibVFRCalib.d" "ussSWLib\source\ussSwLibVFRCalibFlow.d" "ussSWLib\source\ussSwLibVFRCalibFlowTemperature.d" 
	-@echo 'Finished clean'
	-@echo ' '

.PHONY: all clean dependents
.SECONDARY:

-include ../makefile.targets

