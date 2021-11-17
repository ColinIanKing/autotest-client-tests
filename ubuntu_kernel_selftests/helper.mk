gettests:
	@echo '$(notdir $(TEST_GEN_PROGS)) $(notdir $(TEST_CUSTOM_PROGS)) $(notdir $(TEST_PROGS))'

getsubdirs:
	@echo '$(SUB_DIRS)'
