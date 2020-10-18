#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>

int main(int argc, char** argv) {
    if (argc < 2) {
        printf("Usage: ./cat filename1 filename2 ... filenameN\n");
        exit(1);
    }

    char* filename;
    int fd;
    char buffer[1];

    for (int i = 1; i < argc; i++) {
        filename = argv[i];

        if ((fd = open(filename, O_RDONLY)) == -1) {
            perror(filename); // file does not exist
            exit(2);
        }

        while (read(fd, &buffer, 1) > 0)
            write(1, buffer, 1); // print to stdout

        close(fd); // close the file descriptor
    }

    return 0;
}