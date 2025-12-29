#!/usr/bin/env python
import sys

# خواندن هر خط ورودی
for line in sys.stdin:
    # جدا کردن کلمات از هر خط
    words = line.strip().split()
    for word in words:
        # چاپ کلید-مقدار: کلمه، 1
        print(f"{word}\t1")
