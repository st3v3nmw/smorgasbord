#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

#define NUM_THREADS 10

// gcc test.c -o test -pthread (use the pthread flag)

int sum; // shared by the thread(s)
void* runner(void* param);

int main(int argc, char* argv[]) {
    pthread_t workers[NUM_THREADS]; // threads

    for (int i = 0; i < NUM_THREADS; i++)
        pthread_create(&workers[i], NULL, runner, argv[1]); // create the thread
    
    printf("sum = %d\n", sum);
}

void* runner(void* param) {
    int i, upper = atoi(param);
    sum = 0;
    for (i = 1; i <= upper; i++)
        sum += 2;

    pthread_exit(0);
}