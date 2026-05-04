```python
for i in range(len(items) + 1):
    print(items[i])  # IndexError

for i in range(len(items)):
    print(items[i])
```

**Python**：
```python
result = get_data()
print(result.value)  # AttributeError

result = get_data()
if result is not None:
    print(result.value)
```

**JavaScript**：
```javascript
const user = getUser();
console.log(user.name);  // TypeError

console.log(user?.name);
```

**Python**：
```python
f = open("file.txt")
content = f.read()

with open("file.txt") as f:
    content = f.read()
```

```python
if os.path.exists("file.txt"):
    with open("file.txt") as f:
        content = f.read()

try:
    with open("file.txt") as f:
        content = f.read()
except FileNotFoundError:
    content = None
```

```python
def calculate(x, y):
    result = x + y

def calculate(x, y):
    return x + y
```

**Python**：
```python
if x = 5:  # SyntaxError

if x == 5:
```

```python
if 0.1 + 0.2 == 0.3:  # False

if abs((0.1 + 0.2) - 0.3) < 1e-9:

import math
if math.isclose(0.1 + 0.2, 0.3):
```

```python
result = ""
for item in items:
    result += str(item)

result = "".join(str(item) for item in items)
```

```python
def append(item, items=[]):
    items.append(item)
    return items

def append(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

```python
funcs = [lambda: i for i in range(3)]

funcs = [lambda i=i: i for i in range(3)]
```

```python
items = [1, 2, 3, 4]
for item in items:
    if item % 2 == 0:
        items.remove(item)

items = [item for item in items if item % 2 != 0]

for item in items[:]:
    if item % 2 == 0:
        items.remove(item)
```

```javascript
class Counter {
  count = 0;
  increment() {
    setTimeout(function() {
    }, 100);
  }
}

class Counter {
  count = 0;
  increment() {
    setTimeout(() => {
    }, 100);
  }
}
```

```javascript
async function getData() {
  const response = await fetch(url);
}

async function getData() {
  try {
    const response = await fetch(url);
    return await response.json();
  } catch (error) {
    throw error;
  }
}
```

```javascript
const arr1 = [1, 2, 3];
const arr2 = arr1;

const obj1 = { a: 1 };
```

```python
import threading

lock1 = threading.Lock()
lock2 = threading.Lock()

def thread1():
    with lock1:
        with lock2:

def thread2():
    with lock2:
```

```python
counter = 0

def increment():
    global counter

counter = 0
lock = threading.Lock()

def increment():
    global counter
    with lock:
        counter += 1
```
