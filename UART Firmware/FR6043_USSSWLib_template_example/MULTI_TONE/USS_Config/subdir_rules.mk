################################################################################
# Automatically-generated file. Do not edit!
################################################################################

SHELL = cmd.exe

# Each subdirectory must supply rules for building sources it contributes
USS_Config/%.obj: ../USS_Config/%.c $(GEN_OPTS) | $(GEN_FILES) $(GEN_MISC_FILES)
	@echo 'Building file: "$<"'
	@echo 'Invoking: MSP430 Compiler'
	"C:/ti/ccs2041/ccs/tools/compiler/ti-cgt-msp430_21.6.1.LTS/bin/cl430" -vmspx --data_model=large -O3 --use_hw_mpy=F5 --include_path="C:/ti/ccs2041/ccs/ccs_base/msp430/include" --include_path="C:/Users/sasan/workspace_ccstheia/FR6043_USSSWLib_template_example" --include_path="C:/Users/sasan/workspace_ccstheia/FR6043_USSSWLib_template_example/ussSWLib/USS_HAL" --include_path="C:/Users/sasan/workspace_ccstheia/FR6043_USSSWLib_template_example/ussSWLib/source" --include_path="C:/ti/msp/USS_02_30_00_03/USS/include" --include_path="C:/ti/ccs2041/ccs/tools/compiler/ti-cgt-msp430_21.6.1.LTS/include" --advice:power="none" --advice:hw_config=all --define=__MSP430FR6043__ --define=_MPU_ENABLE --define=__EVM430_ID__=0x43 --define=__EVM430_VER__=0x20 --define=__AFE_EXT_3v3__ --define=USS_PULSE_MODE=2 --printf_support=minimal --diag_warning=225 --diag_wrap=off --display_error_number --large_memory_model --silicon_errata=CPU21 --silicon_errata=CPU22 --silicon_errata=CPU40 --preproc_with_compile --preproc_dependency="USS_Config/$(basename $(<F)).d_raw" --obj_directory="USS_Config" $(GEN_OPTS__FLAG) "$<"
	@echo 'Finished building: "$<"'
	@echo ' '


