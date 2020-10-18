#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <string.h>

void* create_shared_memory(size_t size) {
    return mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
}

int main() {
    char parent_msg[] = "hello child!";
    char child_msg[] = "bye parent!";

    char* shm = (char *) create_shared_memory(1024);
    memcpy(shm, parent_msg, sizeof(parent_msg));

    pid_t pid = fork();

    if (pid == 0) {
        printf("Child read: %s\n", shm);
        memcpy(shm, child_msg, sizeof(child_msg));
        printf("Child wrote: %s\n", shm);
    } else {
        printf("Parent read: %s\n", shm);
        sleep(1);
        printf("After sleeping for 1s, parent read: %s\n", shm);
    }
    return 0;
}