#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>


main(int argc, char **argv)
{
	int fd;
	char buf[32];

	if (argc < 2) {
		fprintf(stderr, "Not enough arguments!\n");
		exit(1);
	}

	fd = open(argv[1], O_CREAT | O_TRUNC | O_RDWR, 0666);
	if (fd < 0) {
		fprintf(stderr, "Failed to create %s\n", argv[1]);
		exit(1);
	}
	(void)unlink(argv[1]);

	memset(buf, 0xff, sizeof(buf));

	if (lseek(fd, 1024 * 4096, SEEK_SET) < 0) {
		fprintf(stderr, "Failed to seek to 1024 x 4096: %d %s\n",
			errno, strerror(errno));
		close(fd);
		exit(1);
	}
	if (write(fd, buf, sizeof(buf)) < 0) {
		fprintf(stderr, "Failed to write: %d %s\n",
			errno, strerror(errno));
		close(fd);
		exit(1);
	}
	if (lseek(fd, -512 * 4096, SEEK_CUR) < 0) {
		fprintf(stderr, "Failed to seek back 512 x 4096: %d %s\n",
			errno, strerror(errno));
		close(fd);
		exit(1);
	}
	if (write(fd, buf, sizeof(buf)) < 0) {
		fprintf(stderr, "Failed to write: %d %s\n",
			errno, strerror(errno));
		close(fd);
		exit(1);
	}
	if (lseek(fd, -768 * 4096, SEEK_END) < 0) {
		fprintf(stderr, "Failed to seek back 768 x 4096 from SEEK_END: %d %s\n",
			errno, strerror(errno));
		close(fd);
		exit(1);
	}
	if (write(fd, buf, sizeof(buf)) < 0) {
		fprintf(stderr, "Failed to write: %d %s\n",
			errno, strerror(errno));
		close(fd);
		exit(1);
	}

	close(fd);

	exit(0);
}
