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
    unsigned int length_mod = array_size - 1;

    register unsigned int store_times = 1 << 27;

    register int *a = new int[array_size];
    
    for(unsigned int gourp_num = 4; gourp_num <= 256; gourp_num = gourp_num << 1){
        register unsigned int step_len = (array_size / gourp_num) << 1;
        register unsigned int step = step_len << 2;

        begin = clock();
        for (register int j = 0; j < store_times; j++) {
            a[step] += 1;
            step = (step + step_len) & length_mod;
        }
        end = clock();

        cout << "test number of groups = " << gourp_num << ", ";
        cout << "step len " << step_len << " ";
        cout << "time " << (double)(end - begin) / CLOCKS_PER_SEC * 1000 << " ms\n";
    }

    delete [] a;
    return 0;
}

