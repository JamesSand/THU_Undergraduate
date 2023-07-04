#include <stdio.h>
#include <stdlib.h>

void dangerous_get_function(){
    char buf[4];
    gets(buf);
}

void target(){
    puts("Success!\n");
    exit(-1);
}

int main(){
    dangerous_get_function();
    puts("Fail!\n");
    return 0;
}