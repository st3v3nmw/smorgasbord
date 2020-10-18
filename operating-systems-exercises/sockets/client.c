#include <sys/socket.h>
#include <stdio.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>

#define PORT 6013

int main() {
    int sockfd = socket(AF_INET, SOCK_STREAM, 0); // create a socket
    if (sockfd == -1) { // check if the socket was created successfully
        fprintf(stderr, "Creation of socket failed.\n");
        exit(1);
    }

    // add the connection address and port
    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = inet_addr("127.0.0.1");
    address.sin_port = htons(PORT);

    // connect to the server
    int connection = connect(sockfd, (struct sockaddr *) &address, sizeof(address));

    char buffer[1024];
    char agent[] = "C Client\n";
    write(sockfd, agent, strlen(agent)); // send the client name
    read(sockfd, buffer, 1024); // read the data received from the server and write it to the buffer
    printf("%s\n", buffer); // print the received data to stdout
    return 0;
}