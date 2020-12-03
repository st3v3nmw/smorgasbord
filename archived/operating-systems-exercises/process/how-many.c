#include <stdio.h>
#include <unistd.h>

// how many children are created? 7.
int main()
{
    pid_t c1 = fork(); // root_parent creates c1 (1)
    pid_t c2 = fork(); // root_parent creates c2, c1 creates c3 (2)
    pid_t c3 = fork(); // root_parent creates c4, c1 creates c5, c2 creates c6, c3 creates c7 (4)
    return 0;
}