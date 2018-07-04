# pytrace

pytrace is a simple program to print out a trace of a Python program as
it runs. That is, it displays the values of variables as they are
modified (although it does not display all variables by default).

## Installation

pytrace is currently distributed as a single file – download it and put
it somewhere you can execute it easily. pytrace was written and tested
with Python 3.6; higher versions may work, but lower versions will not.

## Usage

Simply run `pytrace.py` with the name of the file you'd like to trace.
For example:

```
python3.6 pytrace.py my_script.py
```

This would produce output that looks something like this:

```
--> <module>
  <no variables>
  a = 1
  a = 1, b = 2
  a = 3, b = 2
<-- <module> (returned None)
```

More options are available; see the output of `pytrace.py -h`.

## Limitations

pytrace was written in an afternoon, and is intended as a demonstration
of Python's debugging capabilities. It is not meant as a serious
debugging tool. As such, there are several situations where it is known
to produce incorrect output, and it's likely that there are many more
ways to confuse pytrace into misbehaving.

If your code uses the `global` keyword, pytrace is likely to display the
wrong value of variables at various points. Any modifications to global
variables won't be shown until the end of the scope in which they're
made global. A concrete example:

```python
foo = "global value"
bar = "global value"

def do_something():
    global foo
    foo = "local value"
    bar = "local value"

do_something()
```

The above code is traced like this:

```
--> <module>
  <no variables>
  foo = 'global value'
  foo = 'global value', bar = 'global value'
  --> do_something
    bar = 'local value', foo = 'global value'
  <-- do_something (returned None)
  foo = 'local value', bar = 'global value'
<-- <module> (returned None)
```

Note the missing change from `foo = "global value"` to `foo = "local
value"` inside `do_something`, and the fact that it is displayed
correctly after the function returns.

Further, pytrace has not been tested at all with imports or classes;
it's likely that, due to pytrace's simple idea of scope, some variables
will be displayed incorrectly.

Patches to improve this are welcome!

## Copyright

Copyright © 2018 Ash Holland. Licensed under the EUPL (1.2 or later).
