# some credit/reference to https://lptk.github.io/programming/2019/10/15/simple-essence-y-combinator.html

from functools import partial

def lift_self(base):

  def base_lift_self(rec_lift_self, base):

    def applied_self(*args):
      rec = rec_lift_self(rec_lift_self, base)
      return base(rec, *args)

    return applied_self

  return base_lift_self(base_lift_self, base)

@lift_self
def fib(self, n):

  if n == 0 or n == 1:
    return 1
  else:
    return self(n-1) + self(n-2)

for n in range(0,9):
  print(fib(n))

print("===")

foo = fib

del lift_self
del fib

for n in range(0,9):
  print(foo(n))

print("===")

