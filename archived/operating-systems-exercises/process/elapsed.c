#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/time.h>
#include <sys/types.h>

/* determine the amount of time necessary to run a command from the command line */
int main(int argc, char** argv) {
    if (argc != 2) {
        printf("Usage: ./elapsed command\n");
        exit(1);
    }

    struct timeval start_time, end_time;
    gettimeofday(&start_time, NULL);

    pid_t pid = fork(); // fork a child

    printf("%d\n", pid);

    if (pid < 0) {
        fprintf(stderr, "Fork Failed");
        exit(2);
    } else if (pid == 0) { // child process goes here
        execlp(("/bin/%s", argv[1]), argv[1], NULL);
    } else { // parent process goes here
        wait(NULL);

        gettimeofday(&end_time, NULL);
        printf("Time Elapsed: %f seconds\n", end_time.tv_sec - start_time.tv_sec + (end_time.tv_usec - start_time.tv_usec) / 1e6);
    }

    return 0;
}