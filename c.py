
# demonstrates use of globals

def fib(n):
  if n == 0 or n == 1:
    return 1
  else:
    myself = globals()["fib"]
    return myself(n-1) + myself(n-2)

for n in range(0,7):
  print(fib(n))

print("===")

foo = fib
del fib

for n in range(0,7):
  print(foo(n))

print("===")

