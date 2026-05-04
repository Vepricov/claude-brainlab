"""

"""

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================
# ============================================

def get_item(items, index):
    """
    
    IndexError: list index out of range
    """
    # return items[index]
    
    if 0 <= index < len(items):
        return items[index]
    else:
        return None

# ============================================
# ============================================

def format_message(name, count):
    """
    
    TypeError: can only concatenate str (not "int") to str
    """
    # return name + ": " + count
    
    return f"{name}: {count}"
    # return name + ": " + str(count)

# ============================================
# ============================================

def get_user_info(users, user_id):
    """
    
    KeyError: 'user_123'
    """
    # return users[user_id]
    
    return users.get(user_id, None)
    
    # if user_id in users:
    #     return users[user_id]
    # return None

# ============================================
# ============================================

def process_data(data_provider):
    """
    
    AttributeError: 'NoneType' object has no attribute 'process'
    """
    data = data_provider.get_data()
    
    # return data.process()
    
    if data is not None:
        return data.process()
    else:
        return None

# ============================================
# ============================================

def remove_even_numbers(numbers):
    """
    
    """
    # for num in numbers:
    #     if num % 2 == 0:
    #         numbers.remove(num)
    # return numbers
    
    return [num for num in numbers if num % 2 != 0]
    
    # for num in numbers[:]:
    #     if num % 2 == 0:
    #         numbers.remove(num)
    # return numbers

# ============================================
# ============================================

def debug_with_logging(data):
    """
    """
    
    processed = step1(data)
    
    result = step2(processed)
    
    return result

def step1(data):
    return [x * 2 for x in data]

def step2(data):
    return sum(data)

# ============================================
# ============================================

def safe_divide(a, b):
    """
    """
    try:
        result = a / b
        logger.info(f"{a} / {b} = {result}")
        return result
    except ZeroDivisionError:
        return None
    except TypeError as e:
        return None

# ============================================
# ============================================

def calculate_discount(price, discount_rate):
    """
    """
    
    
    discounted_price = price * (1 - discount_rate)
    
    
    return discounted_price

# ============================================
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("=" * 50)
    
    items = ['a', 'b', 'c']
    print(f"get_item(items, 1) = {get_item(items, 1)}")
    print(f"get_item(items, 10) = {get_item(items, 10)}")
    
    print(f"format_message('Count', 42) = {format_message('Count', 42)}")
    
    users = {'user_1': 'Alice', 'user_2': 'Bob'}
    print(f"get_user_info(users, 'user_1') = {get_user_info(users, 'user_1')}")
    print(f"get_user_info(users, 'user_999') = {get_user_info(users, 'user_999')}")
    
    numbers = [1, 2, 3, 4, 5, 6]
    
    print(f"safe_divide(10, 2) = {safe_divide(10, 2)}")
    print(f"safe_divide(10, 0) = {safe_divide(10, 0)}")
    
    print(f"calculate_discount(100, 0.2) = {calculate_discount(100, 0.2)}")
