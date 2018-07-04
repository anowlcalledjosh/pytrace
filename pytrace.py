#!/usr/bin/env python3.6

# Copyright © 2018 Ash Holland. Licensed under the EUPL (1.2 or later).


import argparse
import dis
import sys
import traceback
from types import FrameType as Frame, TracebackType as Traceback
from typing import Any, cast, Dict, List, NewType, Optional, Tuple, Type, Union


Name = str
Value = Any
Event = NewType("Event", str)


verbose = None
display_dunders = None
display_unrepresentables = None


class StackFrame(Dict[Name, Value]):
    def __str__(self) -> str:
        return ", ".join(f"{k} = {v!r}" for k, v in self.items()) or "<no variables>"


class Stack(List[StackFrame]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.prev_all: Optional[StackFrame] = None

    def get(self, name: Name) -> Value:
        """Retrieve the value of a variable."""
        for frame in reversed(self):
            try:
                return frame[name]
            except KeyError:
                pass
        raise NameError(name)

    def push(self, frame: Frame) -> None:
        """Push a new stack frame onto the stack."""
        # Here we avoid storing uninteresting variables by the following
        # heuristic: variables are uninteresting if their name starts
        # with `__` or if the repr() of their value starts with `<`.
        self.append(
            StackFrame(
                {k: v for k, v in frame.f_locals.items() if not is_ignored_name(k, v)}
            )
        )

    def update(self, frame: Frame) -> None:
        """Update the top-most stack frame."""
        self.pop()
        self.push(frame)

    @property
    def all(self) -> StackFrame:
        """Return the currently-visible variables as a stack frame."""
        result = StackFrame()
        names: List[Name] = []
        for frame in reversed(self):
            for name, value in frame.items():
                if name not in names:
                    result[name] = value
                    names.append(name)
        return result


stack = Stack()


def is_ignored_name(name: Name, value: Value) -> bool:
    if name.startswith("__") and not display_dunders:
        return True
    if repr(value).startswith("<") and not display_unrepresentables:
        return True
    return False


def header(s: str = "") -> None:
    """Print a header."""
    HEADER_LENGTH = 60
    if not s:
        print("-" * HEADER_LENGTH)
        return
    length = (HEADER_LENGTH - len(s) - 2) / 2
    if length.is_integer():
        front = back = "-" * int(length)
    else:
        length = int(length)
        front = "-" * length
        back = "-" * (length + 1)
    print(front, s, back)
    calc_length = len(" ".join([front, s, back]))
    assert calc_length == HEADER_LENGTH, calc_length


def log(*args: Any) -> None:
    """Print the arguments, indented once for each stack frame."""
    print("  " * len(stack) + " ".join(str(x) for x in args))


def trace(
    frame: Frame,
    event: Event,
    arg: Union[None, Value, Tuple[Type[BaseException], BaseException, Traceback]],
):
    if verbose:
        header()
        dis.disco(frame.f_code, frame.f_lasti)
    if event == "call":
        trace_call(frame)
    elif event == "line":
        trace_line(frame)
    elif event == "return":
        arg = cast(Value, arg)
        trace_return(frame, arg)
    elif event == "exception":
        arg = cast(Tuple[Type[BaseException], BaseException, Traceback], arg)
        trace_exception(frame, arg)
    else:
        raise Exception(f"Unhandled event type {event!r}")
    return trace


def trace_call(frame: Frame) -> None:
    global stack
    log(f"--> {frame.f_code.co_name}")
    stack.push(frame)


def trace_line(frame: Frame) -> None:
    stack.update(frame)
    if stack.all != stack.prev_all:
        log(stack.all)
        stack.prev_all = stack.all
    elif verbose:
        log("stack unchanged:", stack.all)

    if verbose:
        log("Stack (top frame first):")
        for i, stackframe in enumerate(reversed(stack), start=1):
            log(f" Frame {-i}: {stackframe}")


def trace_return(frame: Frame, arg: Value) -> None:
    global stack
    trace_line(frame)
    stack.pop()
    log(f"<-- {frame.f_code.co_name} (returned {arg!r})")


def trace_exception(
    frame: Frame, arg: Tuple[Type[BaseException], BaseException, Traceback]
) -> None:
    log("--- exception ---")
    log(f"{traceback.format_exception_only(arg[0], arg[1])[-1]}".rstrip())


def main():
    global verbose, display_dunders, display_unrepresentables
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print extra information as the program runs (e.g. disassembled code)",
    )
    parser.add_argument(
        "--display-dunders",
        action="store_true",
        help="display dunder variables (ones which start with two underscores)",
    )
    parser.add_argument(
        "--display-unrepresentables",
        action="store_true",
        help="display variables without a pretty repr()",
    )
    parser.add_argument("file", help="the file to trace")
    args = parser.parse_args()
    verbose = args.verbose
    display_dunders = args.display_dunders
    display_unrepresentables = args.display_unrepresentables
    with open(args.file) as f:
        text = f.read()
        code = compile(text, args.file, "exec")
        if verbose:
            header("CODE")
            dis.dis(code)
    old_trace = sys.gettrace()
    try:
        sys.settrace(trace)
        exec(code, {})
    finally:
        sys.settrace(old_trace)


if __name__ == "__main__":
    main()
