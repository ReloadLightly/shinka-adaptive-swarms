"""Pure public count-schedule contract for the chapter-aligned MPSO study.

The checker enforces this research interface, not a general Python sandbox.
Module and function-local math imports and ordinary pure numerical builtins are
supported equally; candidate observations are immutable at execution time.
"""
from __future__ import annotations

import ast
import builtins
import hashlib
import math
from pathlib import Path
from types import MappingProxyType

from .cli import simulator_fingerprint

INTERFACE_VERSION = "book_mpso_schedule_v1_count_every_subswarm_update"


class BookScheduleError(ValueError):
    """Invalid candidate; engine attaches objective-query accounting."""


def schedule_fingerprint():
    root = Path(__file__).resolve().parents[2]
    paths = ("src/adaptive_swarms/book_schedule.py", "src/adaptive_swarms/book_mpso.py")
    return {**simulator_fingerprint(), **{p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}}


def validated_count(value):
    if type(value) is not int or not 0 <= value <= 5:
        raise BookScheduleError("choose_temporary_quantum_count must return a Python integer from 0 through 5 (not bool)")
    return value


PURE_BUILTINS = {name: getattr(builtins, name) for name in (
    "abs", "all", "any", "bool", "dict", "enumerate", "float", "int", "len", "list",
    "max", "min", "pow", "range", "reversed", "round", "sorted", "sum", "tuple", "zip")}


def _immutable_literal(node):
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return False
    def immutable(v):
        return type(v) in (str, int, float, bool, type(None)) or isinstance(v, tuple) and all(immutable(x) for x in v)
    return immutable(value)


def inspect_schedule_source(source):
    tree = ast.parse(source)
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    if not any(isinstance(n, ast.FunctionDef) and n.name == "choose_temporary_quantum_count" for n in tree.body):
        raise BookScheduleError("Candidate must define choose_temporary_quantum_count(observation)")
    math_modules, imported = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name != "math":
                    raise BookScheduleError("Only pure math imports are permitted")
                math_modules.add(alias.asname or "math")
        elif isinstance(node, ast.ImportFrom):
            if node.module != "math" or node.level:
                raise BookScheduleError("Only pure math imports are permitted")
            for alias in node.names:
                if alias.name.startswith("_") or not hasattr(math, alias.name):
                    raise BookScheduleError("Explicit public math imports are required")
                imported.add(alias.asname or alias.name)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and _immutable_literal(node.value):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if all(isinstance(t, ast.Name) for t in targets):
                continue
        raise BookScheduleError("Module scope permits functions, math imports, docstrings and immutable literal constants")
    calls = set(PURE_BUILTINS) | functions | imported
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise BookScheduleError("Private execution internals are outside the numerical contract")
        if isinstance(node, ast.FunctionDef):
            if node.decorator_list or any(not _immutable_literal(v) for v in node.args.defaults + [v for v in node.args.kw_defaults if v is not None]):
                raise BookScheduleError("Function decorators or mutable/computed default state are not permitted")
            if node.name == "choose_temporary_quantum_count" and (len(node.args.args) != 1 or node.args.posonlyargs or node.args.vararg or node.args.kwarg or node.args.kwonlyargs):
                raise BookScheduleError("choose_temporary_quantum_count requires exactly one observation argument")
        if isinstance(node, (ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Delete, ast.While, ast.Yield, ast.YieldFrom, ast.Await)):
            raise BookScheduleError("External, persistent or unbounded mutable execution state is not permitted")
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(n, ast.Attribute) for t in targets for n in ast.walk(t)):
                raise BookScheduleError("Mutation of imported or external state is not permitted")
        if isinstance(node, ast.Attribute):
            pure_math = isinstance(node.value, ast.Name) and node.value.id in math_modules and not node.attr.startswith("_") and hasattr(math, node.attr)
            lookup = isinstance(node.value, ast.Name) and node.attr == "get"
            if not (pure_math or lookup):
                raise BookScheduleError("Only public math attributes and mapping.get are permitted")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id not in calls:
                raise BookScheduleError(f"Unapproved numerical call: {node.func.id}")
            if not isinstance(node.func, (ast.Name, ast.Attribute)):
                raise BookScheduleError("Indirect calls are outside the numerical contract")
    return tree


def _math_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name != "math" or level:
        raise BookScheduleError("Only math is available to the schedule")
    return math


def load_schedule(path):
    path = Path(path)
    try:
        source = path.read_text()
        tree = inspect_schedule_source(source)
        namespace = {"__builtins__": {**PURE_BUILTINS, "__import__": _math_import}, "__name__": "candidate_book_schedule"}
        exec(compile(tree, str(path), "exec"), namespace)
        function = namespace["choose_temporary_quantum_count"]
        def schedule(observation):
            return validated_count(function(MappingProxyType(dict(observation))))
        return schedule
    except Exception as exc:
        exc.objective_queries = 0
        raise
