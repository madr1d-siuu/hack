import time
import random
import string

def generate_correlation_id():
    timestamp = str(int(time.time()))
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"corr_{timestamp}_{random_str}"