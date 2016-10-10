/*
 * Copyright (C) 2016 Canonical
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 */

/*
 *  Author Colin Ian King,  colin.king@canonical.com
 */

#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <limits.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <fcntl.h>
#include <errno.h>
#include <linux/loop.h>

#define MAX_LOOP	(1024)
#define DELAY_US	(1000)
#define LOOP_SIZE	(65536)

double time_now(void)
{
	struct timeval tv;

	if (gettimeofday(&tv, NULL) < 0)
		return -1.0;

	return (double)tv.tv_sec + ((double)tv.tv_usec / 1000000.0);
}


static int loop_write(const int fd, const off_t len, const unsigned int seed)
{
	off_t left = len;
	unsigned int i = seed;

	if (lseek(fd, 0, SEEK_SET) < 0) {
		fprintf(stdout, "loop dev seek faled: %d (%s)\n",
			errno, strerror(errno));
		return -errno;
	}

	while (left > 0) {
		ssize_t n;
		unsigned char buffer[4096];

		memset(buffer, i, sizeof(buffer));

		n = write(fd, buffer, sizeof(buffer));
		if (n < 0) {
			fprintf(stdout, "loop_write failed %d (%s)\n",
				errno, strerror(errno));
			return -errno;
		}

		left -= n;
		i++;
	}
	return 0;
}

static int loop_read(const int fd, const off_t len, const unsigned int seed)
{
	off_t left = len;
	unsigned int i = seed;

	if (lseek(fd, 0, SEEK_SET) < 0) {
		fprintf(stdout, "loop dev seek faled: %d (%s)\n",
			errno, strerror(errno));
		return -errno;
	}

	while (left > 0) {
		ssize_t n;
		unsigned char buffer[4096];

		n = read(fd, buffer, sizeof(buffer));
		if (n < 0) {
			fprintf(stdout, "loop_read failed %d (%s)\n",
				errno, strerror(errno));
			return -errno;
		}

		if ((buffer[0] & 0xff) != (i & 0xff)) {
			fprintf(stdout, "loop_read: data mismatch: %d (read) vs %d (expected)\n",
				buffer[0] & 0xff, i & 0xff);
			return -1;
		}

		left -= n;
		i++;
	}
	return 0;
}

static int loop_create(const off_t len)
{
	int cfd, bfd, lfd, err;
	int devnr[MAX_LOOP];
	size_t i, n;
	char filename[PATH_MAX];
	const pid_t pid = getpid();
	bool failed = false;
	int loop_read_failures = 0;
	int loop_destroy_failures = 0;
	double t1, t2;

	cfd = open("/dev/loop-control", O_RDWR | O_CLOEXEC);
	if (cfd < 0) {
		fprintf(stdout, "can't open /dev/loop-control: %d (%s)\n",
			errno, strerror(errno));
		return -errno;
	}

	t1 = time_now();
	for (n = 0; n < MAX_LOOP; n++) {
		devnr[n] = ioctl(cfd, LOOP_CTL_GET_FREE);
		if (devnr[n] < 0) {
			fprintf(stdout, "ioctl LOOP_CTL_GET_FREE failed %d (%s)\n",
				errno, strerror(errno));
			break;
		}

		snprintf(filename, sizeof(filename), "backing-file-%d-%d", pid, devnr[n]);
		bfd = open(filename, O_SYNC | O_RDWR | O_CLOEXEC | O_CREAT, S_IRUSR | S_IWUSR);
		if (bfd < 0) {
			fprintf(stdout, "can't create backing store file '%s': %d (%s)\n",
				filename, errno, strerror(errno));
			break;
		}
		if (fallocate(bfd, 0, 0, len) < 0) {
			fprintf(stdout, "can't allocate backing store file '%s': %d (%s)\n",
				filename, errno, strerror(errno));
			break;
		}
		(void)loop_write(bfd, len, n);
		(void)fsync(bfd);

		snprintf(filename, sizeof(filename), "/dev/loop%d", devnr[n]);
		lfd = open(filename, O_RDWR);
		if (lfd < 0) {
			fprintf(stdout, "open of loop device %s failed %d (%s)\n",
				filename, errno, strerror(errno));
			(void)close(bfd);
			failed = true;
			break;
		}

		err = ioctl(lfd, LOOP_SET_FD, bfd);
		if (err < 0) {
			fprintf(stdout, "ioctl LOOP_SET_FD failed %d (%s)\n",
				errno, strerror(errno));
			(void)close(bfd);
			failed = true;
			break;
		}

		if (loop_read(lfd, len, n) < 0) {
			loop_read_failures++;
			failed = true;
		}
		(void)close(bfd);
		(void)close(lfd);
	}
	t2 = time_now();

	for (i = 0; i < n; i++) {
		snprintf(filename, sizeof(filename), "/dev/loop%d", devnr[i]);
		lfd = open(filename, O_RDWR);
		if (lfd < 0) {
			fprintf(stdout, "open of loop device %s failed %d (%s)\n",
				filename, errno, strerror(errno));
			(void)close(bfd);
			failed = true;
			break;
		}
		if (loop_read(lfd, len, i) < 0) {
			loop_read_failures++;
			failed = true;
		}
		(void)close(lfd);
	}

	printf("created %zd out of %d loop back devices in %f seconds\n", n, MAX_LOOP, t2 - t1);
	printf("%d loop read failures\n", loop_read_failures);

	t1 = time_now();
	for (i = 0; i < n; i++) {
		snprintf(filename, sizeof(filename), "backing-file-%d-%d", pid, devnr[i]);
		bfd = open(filename, O_RDWR | O_CLOEXEC, S_IRUSR | S_IWUSR);
		if (bfd < 0) {
			fprintf(stdout, "can't re-open backing store file '%s': %d (%s)\n",
				filename, errno, strerror(errno));
			failed = true;
		} else {
			(void)unlink(filename);

			snprintf(filename, sizeof(filename), "/dev/loop%d", devnr[i]);
			lfd = open(filename, O_RDWR);
			if (lfd >= 0) {
				err = ioctl(lfd, LOOP_CLR_FD, bfd);
				if (err < 0) {
					fprintf(stdout, "ioctl LOOP_CLR_FD failed %d (%s)\n",
						errno, strerror(errno));
					failed = true;
					loop_destroy_failures++;
				}
				(void)close(lfd);
			}
			(void)close(bfd);
retry:
			err = ioctl(cfd, LOOP_CTL_REMOVE, devnr[i]);
			if (err < 0) {
				if (errno == EBUSY) {
					usleep(DELAY_US);
					goto retry;
				}
				fprintf(stdout, "ioctl LOOP_CTL_REMOVE failed %d (%s)\n",
					errno, strerror(errno));
				failed = true;
			}
		}
	}
	t2 = time_now();

	printf("delelete %zd out of %zd loop back devices in %f seconds\n", n - loop_destroy_failures, n, t2 - t1);
	printf("%s\n", failed ? "FAILED" : "PASSED");

	(void)close(cfd);

	return failed ? EXIT_FAILURE : EXIT_SUCCESS;
}

int main()
{
	return loop_create(LOOP_SIZE);
}
