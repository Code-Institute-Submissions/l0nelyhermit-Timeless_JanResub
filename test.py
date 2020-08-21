import random

max_capacity_users = 9999
# Issues a random ID number for the account ID
account_number_list = list(range(1,max_capacity_users))
random.shuffle(account_number_list)
number = account_number_list.pop()
print(number)