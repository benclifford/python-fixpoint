# some credit/reference to https://lptk.github.io/programming/2019/10/15/simple-essence-y-combinator.html
# that ^ notes that it defines Z combinator, because Y combinator recurses infinitely
# in python. And maybe it's the Z combinator I've defined here.
# using more python style syntax with explicit function names and closures.


# two examples to use in a mini-talk/blog:
#   i) recursive lambda - so there is no top level name
#  ii) serialising code using (dill/pickle) so there is no top level name

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

k = fix

del fib
del fix

for n in range(0,9):
  print(foo(n))

print("===")

# here's an example of using fix to do recursive lambda:

fix = k

fiblambda = fix(lambda self, n: 1 if n == 0 or n == 1 else self(n-1) + self(n-2))

for n in range(0,9):
  print(fiblambda(n))

