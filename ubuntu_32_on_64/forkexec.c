#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/types.h>
#include <wait.h>

int
main(argc, argv)
    int argc;
    char **argv;
{
     int pid, rpid;
     int st;

     if (argc < 2) {
         fprintf(stderr, "usage: %s command ...\n", argv[0]);
         return (1);
     }
     if ((pid = fork()) < 0) {
         fprintf(stderr, "fork: %s\n", strerror(errno));
         return (1);
     }
     if (pid == 0) {
         execvp(argv[1], &argv[1]);
         fprintf(stderr, "exec: %s\n", strerror(errno));
         return (1);
     }
     while ((rpid = wait(&st)) > 0 && rpid != pid)
         ;
     if (rpid < 0) {
         fprintf(stderr, "wait: %s\n", strerror(errno));
         return (1);
     }
     printf("status 0x%x\n", st);
     return (st);
}
