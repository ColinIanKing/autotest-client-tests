CC=gcc
LDFLAGS=-laio
CFLAGS=-W -Wall

TESTS=aio-dio-invalidate-failure aio-dio-subblock-eof-read \
      aio-free-ring-with-bogus-nr-pages \
      aio-io-setup-with-nonwritable-context-pointer aio-dio-extend-stat
      aio-cve-2016-10044

all: $(TESTS)

aio-dio-invalidate-failure: aio-dio-invalidate-failure.c
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

aio-dio-subblock-eof-read: aio-dio-subblock-eof-read.c
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

aio-free-ring-with-bogus-nr-pages: aio-free-ring-with-bogus-nr-pages.c
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

aio-io-setup-with-nonwritable-context-pointer: aio-io-setup-with-nonwritable-context-pointer.c
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

aio-dio-extend-stat: aio-dio-extend-stat.c
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS) -lpthread

aio-cve-2016-10044: aio-cve-2016-10044.c
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)
