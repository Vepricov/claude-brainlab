```python
if True
    print("missing colon")

if True:
    print("has colon")
```

```python
def test():
	    print("mixed")  # Tab

def test():
    print("spaces")
    print("consistent")
```

```python
print(undefined_var)

my_var = 42
print(my_var)
```

```python
result = "Value: " + 42

result = "Value: " + str(42)
result = f"Value: {42}"
```

```python
my_list = [1, 2, 3]

my_list.append(4)
```

```python
data = {"name": "Alice"}

age = data["age"]  # KeyError

```

```python
items = [1, 2, 3]

item = items[5]  # IndexError

if len(items) > 5:
    item = items[5]
else:
    item = None
```

```python
num = int("abc")

try:
    num = int(input())
except ValueError:
    num = 0
```

```python
import missing_module

# pip install missing-module
```

```python
with open("missing.txt") as f:
    content = f.read()

try:
    with open("file.txt") as f:
        content = f.read()
except FileNotFoundError:
    content = ""
```

```python
try:
    result = dangerous_operation()
except:
    pass

try:
    result = dangerous_operation()
except (ValueError, TypeError) as e:
```

```python
try:
    file = open("data.txt", "r")
    content = file.read()
except FileNotFoundError:
    content = ""
finally:
    if 'file' in locals():
        file.close()
```

```python
with open("data.txt", "r") as file:
    content = file.read()
```

```python
try:
    process_data(data)
except ValueError as e:
```

```python
import traceback

try:
    risky_operation()
except Exception:
    traceback.print_exc()
```

```python
import pdb

pdb.set_trace()

breakpoint()
```

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

```
