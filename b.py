# some credit/reference to https://lptk.github.io/programming/2019/10/15/simple-essence-y-combinator.html

from functools import partial

def fix(base):

  def base_fix(self):

    def tied_fn(*args):
      rec = self(self)
      return base(rec, *args)

    return tied_fn

  return base_fix(base_fix)

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

