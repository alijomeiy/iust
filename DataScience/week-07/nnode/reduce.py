#!/usr/bin/env python
import sys

current_word = None
current_count = 0

# خواندن ورودی‌های ارسال شده توسط Map
for line in sys.stdin:
    word, count = line.strip().split("\t")
    count = int(count)

    # اگر کلمه مشابهی پیدا کردیم، تعداد آن را جمع کنیم
    if word == current_word:
        current_count += count
    else:
        if current_word:
            # چاپ نتیجه برای کلمه قبلی
            print(f"{current_word}\t{current_count}")
        current_word = word
        current_count = count

# چاپ آخرین کلمه
if current_word == word:
    print(f"{current_word}\t{current_count}")
