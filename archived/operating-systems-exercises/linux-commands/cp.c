#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>

int main(int argc, char* argv[]) {
    if (argc != 3) {
        printf("Usage: ./cp infile outfile\n");
        exit(1);
    }

    int in_fd, out_fd; // file descriptors
    char buffer[1];

    if ((in_fd = open(argv[1], O_RDONLY)) == -1) {
        perror(argv[1]); // infile does not exist
        exit(2);
    }

    if ((out_fd = open(argv[2], O_WRONLY | O_EXCL | O_CREAT, 0777)) == -1) {
        perror(argv[2]); // outfile already exist
        exit(3);
    }

    while (read(in_fd, &buffer, 1) > 0)
        write(out_fd, buffer, 1); // write to outfile

    close(in_fd);
    close(out_fd);

    return 0;
}