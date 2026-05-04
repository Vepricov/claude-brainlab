### 1. Command Not Found

```bash
pyhon script.py  # command not found

python script.py

export PATH="/usr/local/bin:$PATH"
mycommand
```

### 2. Syntax Error

```bash
if [ 1 -eq 1 ]
echo "yes"  # syntax error

if [ 1 -eq 1 ]; then
    echo "yes"
fi
```

### 3. Permission Denied

```bash
chmod +x script.sh

bash script.sh
```

```bash
#!/bin/bash

name="John"
echo "Hello $name"

# + name=John
# + echo 'Hello John'
# Hello John
```

```bash
#!/bin/bash

echo "This won't run"
```

```bash
#!/bin/bash

```

```bash
#!/bin/bash

```

```bash
#!/bin/bash
trap 'echo "Script exited with code $?"' EXIT

trap 'echo "Error on line $LINENO"' ERR

trap 'echo "Interrupted"; cleanup' INT
```

```bash
if [ $? -eq 0 ]; then
    echo "Success"
else
    echo "Failed"
fi

command || { echo "Failed"; exit 1; }

command && echo "Success" || echo "Failed"
```

```bash
die() {
    local message=$1
    echo "Error: $message" >&2
    exit 1
}

[ -f "$file" ] || die "File not found: $file"
```

```bash
#!/bin/bash
[ $# -ge 1 ] || die "Usage: $0 <arg1> [arg2]"

[ -f "$1" ] || die "File not found: $1"

[ -d "$2" ] || die "Directory not found: $2"
```

```bash
#!/bin/bash
#!/usr/bin/env bash
```

```bash
#!/bin/bash
set -euo pipefail
```

```bash
echo "$var"
```

```bash
if [[ $name == "John" ]]; then
if [[ -f $file && $size -gt 100 ]]; then
```

```bash
result=$(command1 $(command2))
```

```bash
my_function() {
    local arg1=$1
    local arg2=$2
}

my_function "value1" "value2"
```

```bash
brew install shellcheck  # macOS
apt install shellcheck   # Ubuntu

shellcheck script.sh
```
