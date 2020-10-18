#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/shm.h>
#include <sys/stat.h>
#include <sys/mman.h>

#define SIZE 4096

// gcc test.c -o test -lrt (use the lrt flag)
// couldn't get this to work

int main() {
    int fd = shm_open("shm", O_RDONLY, 0666);
    char *ptr;
    ptr = (char *) mmap(NULL, SIZE, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, fd, 0); // memory map the shared object
    printf("%s", (char *) ptr);
    shm_unlink("shm"); // remove the shareed memory object
    return 0;
}