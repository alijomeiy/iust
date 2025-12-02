#include <stdio.h>
#include "config.h"

#ifdef CONFIG_FEATURE_HELLO
void feature_hello(void);
#endif

#ifdef CONFIG_FEATURE_MATH
int feature_add(int a, int b);
#endif

int main(void)
{
    printf("Demo app started.\n");

#ifdef CONFIG_USER_NAME
    printf("Configured user name: %s\n", CONFIG_USER_NAME);
#endif

#ifdef CONFIG_FEATURE_HELLO
    feature_hello();
#else
    printf("FEATURE_HELLO is disabled.\n");
#endif

#ifdef CONFIG_FEATURE_MATH
    int result = feature_add(2, 3);
    printf("2 + 3 = %d (FEATURE_MATH enabled)\n", result);
#else
    printf("FEATURE_MATH is disabled.\n");
#endif

    return 0;
}
