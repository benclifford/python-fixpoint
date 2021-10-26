def fib(n):
  if n == 0 or n == 1:
    return 1
  else:
    return fib(n-1) + fib(n-2)

for n in range(0,7):
  print(fib(n))

print("===")

from dill import dump

with open("fib.dill", "wb") as f:
  dump(fib, f)

print("===")
