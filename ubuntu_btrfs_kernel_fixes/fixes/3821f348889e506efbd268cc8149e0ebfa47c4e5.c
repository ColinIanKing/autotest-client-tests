#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <setjmp.h>

#if !defined(__O_TMPFILE)
#define __O_TMPFILE 020000000
#endif
#if !defined(O_TMPFILE)
#define O_TMPFILE (__O_TMPFILE | O_DIRECTORY)
#define O_TMPFILE_MASK (__O_TMPFILE | O_DIRECTORY | O_CREAT)
#endif

static sigjmp_buf jmp_env;

static void sighandler(int dummy)
{
	(void)dummy;
}

main(int argc, char **argv)
{
	int fd;
	struct sigaction new_action;
	char buffer[1024 * 1024];
	int ret;

	if (argc < 2) {
		fprintf(stderr, "Not enough arguments!\n");
		exit(1);
	}

	memset(&new_action, 0, sizeof new_action);
	new_action.sa_handler = sighandler;
	sigemptyset(&new_action.sa_mask);
	new_action.sa_flags = 0;
	if (sigaction(SIGUSR1, &new_action, NULL) < 0) {
		fprintf(stderr, "sigaction failed!\n");
		exit(1);
	}

	fd = open(argv[1], O_RDWR | O_TMPFILE);
	if (fd < 0) {
		fprintf(stderr, "Failed to create %s\n", argv[1]);
		exit(1);
	}


	memset(buffer, 0, sizeof(buffer));
	(void)write(fd, buffer, sizeof(buffer));
	sync();
	ret = sigsetjmp(jmp_env, 1);
	if (ret == 0)
		sleep(60);
	(void)unlink(argv[1]);
	close(fd);
	exit(0);
}
