/*
 *  From https://www.spinics.net/lists/linux-block/msg28507.html
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <sys/uio.h>

#define PAGE_SIZE 4096
#define SECT_SIZE 512
#define BUF_OFF (2*SECT_SIZE)

int main(int argc, char **argv)
{
	int fd = open(argv[1], O_RDWR | O_DIRECT);
	int ret;
	char *buf;
	loff_t off;
	struct iovec iov[2];
	unsigned int seq;

	if (fd < 0) {
		perror("open");
		return 1;
	}

	off = strtol(argv[2], NULL, 10);

	posix_memalign((void **)&buf, PAGE_SIZE, PAGE_SIZE);

	iov[0].iov_base = buf;
	iov[0].iov_len = SECT_SIZE;
	iov[1].iov_base = buf + BUF_OFF;
	iov[1].iov_len = SECT_SIZE;

	seq = 0;
	memset(buf, 0, PAGE_SIZE);

	while (1) {
		*(unsigned int *)buf = seq;
		*(unsigned int *)(buf + BUF_OFF) = seq;
		ret = pwritev(fd, iov, 2, off);
		if (ret < 0) {
			perror("pwritev");
			return 1;
		}
		if (ret != 2*SECT_SIZE) {
			fprintf(stderr, "Short pwritev: %d\n", ret);
			return 1;
		}
		ret = pread(fd, buf, PAGE_SIZE, off);
		if (ret < 0) {
			perror("pread");
			return 1;
		}
		if (ret != PAGE_SIZE) {
			fprintf(stderr, "Short read: %d\n", ret);
			return 1;
		}
		if (*(unsigned int *)buf != seq ||
		    *(unsigned int *)(buf + SECT_SIZE) != seq) {
			printf("Lost write %u: %u %u\n", seq, *(unsigned int *)buf, *(unsigned int *)(buf + SECT_SIZE));
			return 1;
		}
		seq++;
	}

	return 0;
}
