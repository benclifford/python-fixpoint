from dill import load

with open("fiblambda.dill", "rb") as f:
  fib = load(f)

for n in range(0,7):
  print(fib(n))

print("===")

del fib

with open("fiblambda.dill", "rb") as f:
  user_supplied_function = load(f)

for n in range(0,7):
  print(user_supplied_function(n))


