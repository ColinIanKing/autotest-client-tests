SUBDIRS := $(wildcard */.)
TARGETS := all clean

SUBDIRS_TARGETS := \
    $(foreach t,$(TARGETS),$(addsuffix $t,$(SUBDIRS)))

.PHONY : $(TARGETS) $(SUBDIRS_TARGETS)

$(TARGETS) : % : $(addsuffix %,$(SUBDIRS))
$(SUBDIRS_TARGETS) :
	$(MAKE) -C $(@D) $(@F:.%=%)
