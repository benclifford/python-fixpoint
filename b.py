# some credit/reference to https://lptk.github.io/programming/2019/10/15/simple-essence-y-combinator.html

from functools import partial

def fix(base):

  def base_lift_self(rec_fix, base):

    def looped_base(*args):
      rec = rec_fix(rec_fix, base)
      return base(rec, *args)

    return looped_base

  return base_lift_self(base_lift_self, base)

@fix
def fib(self, n):

  if n == 0 or n == 1:
    return 1
  else:
    return self(n-1) + self(n-2)

for n in range(0,9):
  print(fib(n))

print("===")

foo = fib

del fix
del fib

for n in range(0,9):
  print(foo(n))

print("===")

