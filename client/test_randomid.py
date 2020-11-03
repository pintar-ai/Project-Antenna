import random 
import string

size = 12 
chars = string.ascii_uppercase + string.digits

random_id = ''.join(random.choice(chars) for _ in range(size))
print (random_id)