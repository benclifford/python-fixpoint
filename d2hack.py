from dill import load

with open("fib.dill", "rb") as f:
  user_supplied_function = load(f)

fib = user_supplied_function

for n in range(0,7):
  print(user_supplied_function(n))


