# Breaking recursion in Python and `fix`-ing it back up again

Theoreticians like to define simple programming languages, for example the lambda calculus, and in some parts of that theoretical world, you can't call a function if you haven't defined it yet. If I want to call `f` in another function `g`, I have to first define `f()` before defining `g()`:

```python3
def f():
  retun 3

def g():
  return f()+1
```

This breaks recursion: you can't call yourself, because you haven't finished defining yourself yet.

Luckily in most languages, that isn't a problem - theory be damned, this Python code runs just fine:

```python3
def fib(n):
  if n == 0 or n == 1:
    return 1
  else:
    return fib(n-1) + fib(n-2)

for n in range(0,7):
  print(fib(n))    
```

```
1
1
2
3
5
8
13
```

I wondered about the specific additions Python makes to lambda calculus that make the above recursion work, and this repo is the result of those musings.

## Recursion in Python

Why does the above work without `fib` being defined first?

Because Python doesn't need the definition of a function being called until you actually run the containing code and reach the call site. By the time `fib` can actually be executed and reach a (recursive) call to `fib`, it has already been fully defined. (that's why it can be called in the first place).

When function execution reaches a call to `fib` (or any other function) it looks up the name to find the function to execute. This can be made a bit more explicit in the above example by separating out the lookup of `fib` from the invokation of whatever comes out of that lookup:

```python3
def fib(n):
  if n == 0 or n == 1:
    return 1
  else:
    myself = globals()["fib"]
    return myself(n-1) + myself(n-2)
```

So, when `fib` runs, it doesn't call *itself* as such, but asks the global environment for the name of a function called <code>fib</code> and calls that. And in most cases, that really is itself, the right function, and everything works.

## Breaking recursion

So how can we break this?

I'll start with a first quite contrived example: rename `fib`:

```python3
foo = fib

del fib

for n in range(0,7):
  print(foo(n))

```

This will break after a few steps:

```
1
1
Traceback (most recent call last):
  File "a.py", line 18, in &lt;module>
    print(foo(n))
  File "a.py", line 7, in fib
    return fib(n-1) + fib(n-2)
NameError: global name 'fib' is not defined
```

Boom! This code prints the first two values correctly (because no recursion is needed) but as soon as the code tries to recurse, it explodes: even though the function is called `foo` now, it is still trying to call `fib` to recurse - it isn't calling itself, remember.</p>

Recursive code, at least in this style, is reliant on an in-scope dictionary entry that aligns with the function definition: a recursive function isn't a free-standing object, in the way that a non-recursive function is.

## Less Contrived Examples

Here are a couple of more practical cases where this dictionary tie causes problems: first writing recursive functions usign `lambda` expressions, and second serialising functions using `dill` (for example to send over a network for execution).

In the first example, I'm going to try defining fibonnacci as a lambda expression. I want to write some code like this:

```python3
  for n in range(0,7):
    print( (lambda n: _) (n) )
```

In that example, `_` is some code that still needs writing. The base cases are easy:

```python3
lambda n: 1 if n == 0 or n == 1 else _
```

The recursive case `_` remains to be defined. Here, the lambda needs to call itself. But how? There's no reference anywhere to itself. So it looks like recursive lambda expressions are impossible.


The next example is serialising functions using `dill` and then trying to deserialise and execute them elsewhere. This is something that happens a lot in one of my work projects (<a href="http://parsl-project.org/">Parsl</a>) which aims to help you run Python code distributed across many computers.

The first bit of code defines recursive <code>fib</code> as before and serialises it out to a file:

```python3
def fib(n):
  if n == 0 or n == 1:
    return 1
  else:
    return fib(n-1) + fib(n-2)

from dill import dump

with open("fib.dill", "wb") as f:
  dump(fib, f)
```

The second bit of code loads that serialised function from a file, and tries to run it in a loop:

```python3
with open("fib.dill", "rb") as f:
  user_supplied_function = load(f)

for n in range(0,7):
  print(user_supplied_function(n))
```

It would be nice if this behaves like the first example, but with definition and execution separated by a serialisation/deserialisation. (In the Parsl case, more interesting things would happen to the serialised form first: it could be moved and copied to many different machines, for example)


Like the `del` example above, this works for the first two non-recursive results, but fails as soon as recursion happens:

```python3
1
1
Traceback (most recent call last):
  File "d2.py", line 17, in &lt;module>
    print(user_supplied_function(n))
  File "d1.py", line 5, in fib
    return fib(n-1) + fib(n-2)
NameError: name 'fib' is not defined
```

The function is trying to recurse using the name <code>fib</code> still, even though that name isn't defined anywhere on the execution side - on the execution side, it happens to be called `user_supplied_function`.

## Fixing this

The above examples are intended to show the core of the problem: a function needs a reference to itself in order to recurse, and getting that reference from the environment is not always possible.


What other ways could a function get a reference to itself? One clunky way is if the function takes itself as an argument, like this: 

```python3
def fib(myself, n):
  if n == 0 or n == 1:
    return 1
  else:
    return myself(myself, n-1) + myself(myself, n-2)

for n in range(0,7):
  print(fib(fib, n))
```

That changes the calling convention into something weird looking, and different from what a normal Python function invocation looks like - but at least `fib` doesn't make use of any global binding.

This new calling convention makes the `dill` example work.

It also makes the `lambda` almost possible. The expression needs binding to a name somewhere, in order to be passed into itself, but the name doesn't matter - it becomes an entirely local issue, different inside the lambda expression (`myself`) from outside (`f`):

```python3
for n in range(0,7):
  f = lambda myself, n: 1 if n==0 or n==1 else myself(myself, n-1) + myself(myself, n-2)
  print(f(f, n))
```

## Decorators

There's a way to abstract away that calling convention using decorators.

Decorators are Python syntax that lets you pass a function definition through some of your own code before it is bound to the global name of the function.

For example, this:

```python3
@fix
def fib(myself, n):
  if n == 0 or n == 1:
    return 1
  else:
    return myself(n-1) + myself(n-2)
```

which means something similar to (but not quite) this non-decorator code:

```python3
def _fib(myself, n):
  if n == 0 or n == 1:
    return 1
  else:
    return myself(n-1) + myself(n-2)

fib = fix(_fib)
```

`fix` is a function which itself takes a function, and returns a replacement for that function.

I'm going to make `fix` wire stuff up so that you can invoke `fib` *without* that special calling convention, like at the start of this document, but make it so `fib` receives a reference to itself in the `myself` parameter as if we *are* using that special calling convention.

## Defining `fix`

Here is a definition of `fix` that works:

```python3
def fix(base):

  def base_fix(self):

    def tied_fn(*args):
      rec = self(self)
      return base(rec, *args)

    return tied_fn

  return base_fix(base_fix)
```

It turns out to be a lot of wiring of names and values around without much else seemingly happening. Perhaps that should be unsurprising: The core of the recursion problem above is about getting the function definition wired through to the right place.

The supplied base function, eg `fib` in the concrete example, is replaced by `tied_fn` which calls the base function with an extra argument on the front, to fit the special calling convention.

That extra argument on the front is almost but not quite the function itself: instead it's the result of performing this knot tying one more time, so that every time it is invoked, it always adds on the appropriate extra parameter.

Using this, it's possible to even combine both of the examples above and make a recursive `lambda` fibonacci that can be serialised between processes.

The definition:  
  
```python3
fiblambda = fix(lambda self, n: 1 if n == 0 or n == 1 else self(n-1) + self(n-2))
from dill import dump
with open("fiblambda.dill", "wb") as f:
  dump(fiblambda, f)
```

... and the execution:

```python3
with open("fiblambda.dill", "rb") as f:
  user_supplied_function = load(f)

for n in range(0,7):
  print(user_supplied_function(n))
```

<hr>

So in summary: regular Python recursion only works if your functions have well defined names. This is how things work in most programming, but I gave a couple of examples (`lambda` and `dill`) where that isn't true. Then some programming language theory magic (expressed as a decorator) lets you make recursive functions that don't need to know their own name.

Another place in Python where some of this distinction between name and content in recursion comes into play is with recursive module import: you can make recursive module imports using `import x` and later referencing `x.y` but you can't using `from x import y`. The different between these imports is that in the first example, `y` isn't looked up until it is used, much later on when the recursive import is finished. Using `from` syntax, `x` needs to be completely imported before the statement can continue, which breaks recursion.

That `fix` decorator is something like the <a href="https://en.wikipedia.org/wiki/Fixed-point_combinator#Strict_fixed-point_combinator">Z combinator</a> but I've avoided mention of this until the end, because I wanted all my examples to be grounded in Python code.


