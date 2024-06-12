import hashlib
import random


def generate_short_link():
    random_number = random.randint(0, 10000)
    hash_object = hashlib.md5(str(random_number).encode())
    return hash_object.hexdigest()[:3]
