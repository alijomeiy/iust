#include <stdio.h>
#include "config.h"

void feature_hello(void)
{
#ifdef CONFIG_USER_NAME
    printf("Hello, %s! FEATURE_HELLO says hi.\n", CONFIG_USER_NAME);
#else
    printf("Hello! FEATURE_HELLO is enabled but USER_NAME is not set.\n");
#endif
}
