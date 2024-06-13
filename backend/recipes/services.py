import hashlib
import random


def generate_short_link():
    random_number = random.randint(0, 10000)
    hash_object = hashlib.md5(str(random_number).encode())
    return hash_object.hexdigest()[:3]


def get_unique_short_link(model_class):
    short_link = generate_short_link()
    while model_class.objects.filter(short_link=short_link).exists():
        short_link = generate_short_link()
    return short_link
