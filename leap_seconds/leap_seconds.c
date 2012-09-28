/* Leap second stress test
 *              by: john stultz (johnstul@us.ibm.com)
 *              (C) Copyright IBM 2012
 *              Licensed under the GPLv2
 *
 *  This test signals the kernel to insert a leap second
 *  every day at midnight GMT. This allows for stessing the
 *  kernel's leap-second behavior, as well as how well applications
 *  handle the leap-second discontinuity.
 *
 *  Usage: leap-a-day [-s]
 *
 *  Options:
 *	-s:	Each iteration, set the date to 10 seconds before midnight GMT.
 *		This speeds up the number of leapsecond transitions tested,
 *		but because it calls settimeofday frequently, advancing the
 *		time by 24 hours every ~16 seconds, it may cause application
 *		disruption.
 *
 *  Other notes: Disabling NTP prior to running this is advised, as the two
 *		 may conflict in thier commands to the kernel.
 *
 *  To build:
 *	$ gcc leap-a-day.c -o leap-a-day -lrt
 */



#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>
#include <sys/timex.h>
#include <string.h>
#include <signal.h>

#define NSEC_PER_SEC 1000000000ULL

#define CLOCKID CLOCK_REALTIME
#define SIG SIGRTMIN

#define errExit(msg)    do { perror(msg); exit(EXIT_FAILURE); \
                        } while (0)

timer_t             timerid;
struct sigevent     sev;
struct itimerspec   its;
sigset_t            mask;
struct sigaction    sa;
long long           secs;

/* returns 1 if a <= b, 0 otherwise */
static inline int in_order(struct timespec a, struct timespec b)
{
        if(a.tv_sec < b.tv_sec)
                return 1;
        if(a.tv_sec > b.tv_sec)
                return 0;
        if(a.tv_nsec > b.tv_nsec)
                return 0;
        return 1;
}

struct timespec timespec_add(struct timespec ts, unsigned long long ns)
{
	ts.tv_nsec += ns;
	while(ts.tv_nsec >= NSEC_PER_SEC) {
		ts.tv_nsec -= NSEC_PER_SEC;
		ts.tv_sec++;
	}
	return ts;
}


char* time_state_str(int state)
{
	switch (state) {
		case TIME_OK:	return "TIME_OK";
		case TIME_INS:	return "TIME_INS";
		case TIME_DEL:	return "TIME_DEL";
		case TIME_OOP:	return "TIME_OOP";
		case TIME_WAIT:	return "TIME_WAIT";
		case TIME_BAD:	return "TIME_BAD";
	}
	return "ERROR"; 
}

/* clear NTP time_status & time_state */
void clear_time_state(void)
{
	struct timex tx;
	int ret;

	/*
	 * XXX - The fact we have to call this twice seems
	 * to point to a slight issue in the kernel's ntp state
	 * managment. Needs to be investigated further.
	 */

	tx.modes = ADJ_STATUS;
	tx.status = STA_PLL;
	ret = adjtimex(&tx);

	tx.modes = ADJ_STATUS;
	tx.status = 0;
	ret = adjtimex(&tx);
}

/* Make sure we cleanup on ctrl-c */
void handler(int unused)
{
	clear_time_state();
	exit(0);
}


/* Test for known hrtimer failure */
int test_hrtimer_failure(void)
{
	struct timespec now, target;
    int retval = 0;

	clock_gettime(CLOCK_REALTIME, &now);
	target = timespec_add(now, NSEC_PER_SEC/2);
	clock_nanosleep(CLOCK_REALTIME, TIMER_ABSTIME, &target, NULL);
	clock_gettime(CLOCK_REALTIME, &now);

	if (!in_order(target, now)) {
		printf("Note: hrtimer early expiration failure observed.\n");
        retval = 1;
	}
    return retval;
}

static void
timeout_handler(int sig, siginfo_t *si, void *uc)
{
    printf("Timeout reached.\n");
    signal(sig, SIG_IGN);
    exit(0);
}

int
set_timeout(char * timeout)
{
    /* Establish handler for timer signal
    */
    sa.sa_flags = SA_SIGINFO;
    sa.sa_sigaction = timeout_handler;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIG, &sa, NULL) == -1)
        errExit("sigaction");

    /* Block timer signal temporarily
    */
    sigemptyset(&mask);
    sigaddset(&mask, SIG);
    if (sigprocmask(SIG_SETMASK, &mask, NULL) == -1)
        errExit("sigprocmask");

    /* Create the timer
    */
    sev.sigev_notify = SIGEV_SIGNAL;
    sev.sigev_signo = SIG;
    sev.sigev_value.sival_ptr = &timerid;
    if (timer_create(CLOCKID, &sev, &timerid) == -1)
        errExit("timer_create");

    /* Start the timer
    */
    secs = atoll(timeout);
    its.it_value.tv_sec = secs;
    its.it_value.tv_nsec = 0;
    its.it_interval.tv_sec = its.it_value.tv_sec;
    its.it_interval.tv_nsec = its.it_value.tv_nsec;

    if (timer_settime(timerid, 0, &its, NULL) == -1)
         errExit("timer_settime");

    /* Unlock the timer signal, so that timer notification can be delivered
    */
    if (sigprocmask(SIG_UNBLOCK, &mask, NULL) == -1)
        errExit("sigprocmask");

}

int main(int argc, char** argv)
{
	struct timeval tv;
	struct timex tx;
	struct timespec ts;
	int settime = 0;
    int exit_on_error = 0;
    int arg;

	signal(SIGINT, handler);
	signal(SIGKILL, handler);
	printf("This runs continuously. Press ctrl-c to stop\n");

	/* Process arguments */
    for (arg = 1; arg < argc; arg++) {
		if (!strncmp(argv[arg], "-s", 2)) {
			printf("Setting time to speed up testing\n");
			settime = 1;
        } else if (!strncmp(argv[arg], "-e", 2)) {
            printf("Exit on detection of error condition.\n");
            exit_on_error = 1;
        } else if (!strncmp(argv[arg], "-t", 2)) {
            arg++;
            set_timeout(argv[arg]);
		} else {
			printf("Usage: %s [-s] [-x] [-t <sec>]\n", argv[0]);
			printf("\t-s: Set time to right before leap second each iteration.\n");
            printf("\t-x: Exit if the error condition is detected.\n");
            printf("\t-t: Exit the application after running for so many seconds.\n");
		}
	}

	printf("\n");
	while (1) {
		int ret;
		time_t now, next_leap;
		/* Get the current time */
		gettimeofday(&tv, NULL);

		/* Calculate the next possible leap second 23:59:60 GMT */
		tv.tv_sec += 86400 - (tv.tv_sec % 86400);
		next_leap = ts.tv_sec = tv.tv_sec;

		if (settime) {
			tv.tv_sec -= 10;
			settimeofday(&tv, NULL);
			printf("Setting time to %s", ctime(&ts.tv_sec));
		}

		/* Reset NTP time state */
		clear_time_state();

		/* Set the leap second insert flag */
		tx.modes = ADJ_STATUS;
		tx.status = STA_INS;
		ret = adjtimex(&tx);
		if (ret) {
			printf("Error: Problem setting STA_INS!: %s\n",
							time_state_str(ret));
			return -1;
		}

		/* Validate STA_INS was set */
		ret = adjtimex(&tx);
		if (tx.status != STA_INS) {
			printf("Error: STA_INS not set!: %s\n",
							time_state_str(ret));
			return -1;
		}

		printf("Scheduling leap second for %s", ctime(&next_leap));

		/* Wake up 3 seconds before leap */
		ts.tv_sec -= 3;
		if(clock_nanosleep(CLOCK_REALTIME, TIMER_ABSTIME, &ts, NULL))
			printf("Something woke us up, returning to sleep\n");

		/* Validate STA_INS is still set */
		ret = adjtimex(&tx);
		if (tx.status != STA_INS) {
			printf("Something cleared STA_INS, setting it again.\n");
			tx.modes = ADJ_STATUS;
			tx.status = STA_INS;
			ret = adjtimex(&tx);
		}

		/* Check adjtimex output every half second */
		now = tx.time.tv_sec;
		while (now < next_leap+2) {
			char buf[26];
			ret = adjtimex(&tx);

			ctime_r(&tx.time.tv_sec, buf);
			buf[strlen(buf)-1] = 0; /*remove trailing\n */

			printf("%s + %6ld us\t%s\n",
					buf,
					tx.time.tv_usec, 
					time_state_str(ret));
			now = tx.time.tv_sec;
			/* Sleep for another half second */
			ts.tv_sec = 0;
			ts.tv_nsec = NSEC_PER_SEC/2;
			clock_nanosleep(CLOCK_MONOTONIC, 0, &ts, NULL);
		}

		/* Note if kernel has known hrtimer failure */
		if (test_hrtimer_failure() && exit_on_error) {
            exit(1);
        }

		printf("Leap complete\n\n");
	}

	clear_time_state();
	return 0;
}
