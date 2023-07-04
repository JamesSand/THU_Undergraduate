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

    unsigned int test_size = 1 << 10 << 6; // 64 KB
    unsigned int array_size = test_size >> 2;
    unsigned int len_mask = array_size - 1;

    register unsigned int store_times = 1 << 27;

    unsigned int step = 4;

    register int *block = new int[array_size];
    
    for (int i = 0; i < 6; i++) {

        register unsigned int step_len = step >> 2;

        begin = clock();
        for (register int j = 0; j < store_times; j++) {
            block[(j * step_len) & len_mask] += 1;
        }

        end = clock();
        

        cout << "test step " << step << " B ";
        cout << "step len " << step_len << " ";
        cout << "time " << (double)(end - begin) / CLOCKS_PER_SEC * 1000 << " ms\n";
        
        step = step << 1;
    }

    delete [] block;
    return 0;
}
