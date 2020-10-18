#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/time.h>
#include <sys/types.h>
#include <string.h>

#define BUFFER_SIZE 100
#define READ_END 0
#define WRITE_END 1

// pass the child's PID from the parent to the child using a pipe
int main() {
    char write_msg[BUFFER_SIZE] = "Greetings, your PID is";
    char read_msg[BUFFER_SIZE];
    int fd[2];

    if (pipe(fd) == -1) { // create the pipe
        fprintf(stderr, "Pipe failed\n");
        exit(1); 
    }

    pid_t pid = fork();
    char str_pid[8];
    snprintf(str_pid, sizeof(str_pid), " %d", pid);
    strcat(write_msg, str_pid);

    if (pid < 0) {
        fprintf(stderr, "Fork failed\n");
        exit(2);
    } else if (pid == 0) { // child process
        close(fd[WRITE_END]); // close unused end of the pipe
        read(fd[READ_END], read_msg, BUFFER_SIZE);
        printf("read %s\n", read_msg);
        close(fd[READ_END]);
    } else { // parent process
        close(fd[READ_END]); // read unused end of pipe
        write(fd[WRITE_END], write_msg, strlen(write_msg)+1); // write to pipe
        close(fd[WRITE_END]); // close write end of pipe
    }

    return 0;
}