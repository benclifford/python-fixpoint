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


What other ways could a function get a reference to itself? One way that works in some situations is if the function takes its self as an argument, like this: 

</p>
<pre>
def fib(myself, n):
  if n == 0 or n == 1:
    return 1
  else:
    return myself(myself, n-1) + myself(myself, n-2)

for n in range(0,7):
  print(fib(fib, n))
</pre>

<p>That changes the calling convention into something quite ugly - but at least <code>fib</code> doesn't make use of any global binding.
</p>

<p>This helps a bit in the lambda case: a lambda expression can't be passed to itself as an argument without giving it a name somewhere, for example:

</p>

<pre>
for n in range(0,7):
  f = lambda myself, n: 1 if n==0 or n==1 else myself(myself, n-1) + myself(myself, n-2)
  print(f(f, n))
</pre>

<p>
but at least the lambda expression doesn't need to know the name. As long as the awkward calling convention is specified, that lambda expression could be passed around, even serialised using `dill`.
</p>

<hr/>
<p>There's a way to abstract away that awkward calling convention separately from the meat of the recursive function using a decorator. A decorator takes a python function definition, and returns a new function that will be bound to the global name instead of the original function definition.
</p>
<p>For example:
</p>

<pre>
@fix
def fib(self, n):
  if n == 0 or n == 1:
    return 1
  else:
    return self(n-1) + self(n-2)
</pre>

<p>This code will define a function with two parameters, and then pass it at a parameter to <code>fix</code>, and whatever <code>fix</code> returns is what will be bound to the global name <code>fib</code>. This is similar, but not quite the same, as writing this without using <code>@decorator</code> syntax:
 
</p>

<pre>
def _fib(self, n):

  if n == 0 or n == 1:
    return 1
  else:
    return self(n-1) + self(n-2)

fib = fix(_fib)
</pre>

<hr>
<p>So how should <code>fix</code> be defined?</p>

<pre>
def fix(base):

  def base_fix(self):

    def tied_fn(*args):
      rec = self(self)
      return base(rec, *args)

    return tied_fn

  return base_fix(base_fix)
</pre>

<p>It turns out to be a lot of wiring of names around without much else seemingly happening. Perhaps that should be unsurprising: The core of the recursion problem above is about getting the right name in the right place to recurse.</p>

<p>Using this, it's possible to make a recursive fibonacci that can be serialised between processes. And a recursive fibonacci using only <code>lambda</code> and <code>fix</code>, and even a recursive fibonacci defined using lambda that can be serialised between processes:</p>
  
  
<pre>
fiblambda = fix(lambda self, n: 1 if n == 0 or n == 1 else self(n-1) + self(n-2))
from dill import dump
with open("fiblambda.dill", "wb") as f:
  dump(fiblambda, f)
</pre>

<p>... fed into ...</p>

<pre>
with open("fiblambda.dill", "rb") as f:
  user_supplied_function = load(f)

for n in range(0,7):
  print(user_supplied_function(n))
</pre>

<hr>
<p>So 
<p>Another place in Python where some of this distinction between name and content in recursion comes into play is with recursive module import: that works with <code>import</code> but not with <code>from</code> - similar knot tying has to happen with module import and it happens to work one way and not the other.</p>

