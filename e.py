
def fib(myself, n):
  if n == 0 or n == 1:
    return 1
  else:
    return myself(myself, n-1) + myself(myself, n-2)

for n in range(0,7):
  print(fib(fib, n))

