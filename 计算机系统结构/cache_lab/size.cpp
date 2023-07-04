#include <iostream>
#include <time.h>

using namespace std;

int main() {

    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(3, &mask);
    if (sched_setaffinity(0, sizeof(mask), &mask) < 0) {
        perror("sched_setaffinity");
    }

    clock_t begin, end;

    // current size range from 1024 to 2 ^ 12 1024
    unsigned int current_size = 1 << 10;
    register unsigned int store_times = 1 << 27;
    
    for (int i = 0; i < 12; i++) {
        unsigned int test_size = current_size >> 10;
        unsigned int array_size = current_size / sizeof(int);
        
        register int *a = new int[array_size];
        register unsigned int length_mod = array_size - 1;
        begin = clock();
        for (register int j = 0; j < store_times; j++) {
            // a[j << 4 & length_mod] += 1;
            a[j & length_mod] += 1;
        }
        end = clock();
        delete [] a;

        cout << "test size " << test_size << " KB ";
        cout << "array size " << array_size << " ";
        cout << "time " << (double)(end - begin) / CLOCKS_PER_SEC * 1000 << " ms\n";
        
        current_size = current_size << 1;
    }
    return 0;
}