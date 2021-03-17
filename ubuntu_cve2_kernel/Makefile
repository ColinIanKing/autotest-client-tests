SUBDIRS = CVE-2021-2736X

all:
	for subdir in $(SUBDIRS); do \
		make -C $$subdir; \
	done

check:
	for subdir in $(SUBDIRS); do \
		make -C $$subdir check; \
	done

clean:
	for subdir in $(SUBDIRS); do \
		make -C $$subdir clean; \
	done
