#!/bin/sh
# Usage: genconfig.sh .config include/config.h

IN="$1"
OUT="$2"

if [ ! -f "$IN" ]; then
    echo "Input config file '$IN' not found!"
    exit 1
fi

mkdir -p "$(dirname "$OUT")"

# header
echo "/* Auto-generated from .config - DO NOT EDIT */" > "$OUT"

# تبدیل هر خط CONFIG_... به #define مناسب
grep '^CONFIG_' "$IN" | while IFS= read -r line; do
    NAME=$(printf "%s" "$line" | cut -d= -f1)
    VAL=$(printf "%s" "$line" | cut -d= -f2-)

    case "$VAL" in
        y)
            echo "#define $NAME 1" >> "$OUT"
            ;;
        n)
            # غیرفعال؛ چیزی تعریف نمی‌کنیم
            ;;
        \"*\")
            # رشته
            echo "#define $NAME $VAL" >> "$OUT"
            ;;
        *)
            # عدد یا چیز دیگر
            echo "#define $NAME $VAL" >> "$OUT"
            ;;
    esac
done
