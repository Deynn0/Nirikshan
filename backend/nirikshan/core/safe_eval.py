"""Safe declarative expression evaluator for rule logic.

Uses Python's AST module with a strict whitelist — no eval(), no exec().
Supports:
- Comparisons: <, <=, >, >=, ==, !=
- Boolean operators: and, or, not
- Arithmetic: +, -, *, /
- Set membership: `in`, `not in`
- Date arithmetic via date_diff(field, ref_date, 'days'/'years')
- Constants: True, False, None, numeric and string literals

Any expression not on the whitelist raises SafeEvalError immediately.
"""

from __future__ import annotations

import ast
import operator
from datetime import date, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SafeEvalError(Exception):
    """Raised when an expression contains disallowed constructs."""


class EvalTimeoutError(SafeEvalError):
    """Raised when evaluation would exceed operation limit."""


EvalTimeout = EvalTimeoutError


# ---------------------------------------------------------------------------
# Allowed AST node whitelist
# ---------------------------------------------------------------------------

_ALLOWED_NODES = {
    # Literals & constants
    ast.Expression,
    ast.Constant,
    ast.NameConstant,  # Python 3.7 compat – maps to ast.Constant in 3.8+
    # Names (variables)
    ast.Name,
    ast.Load,
    # Operators
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    # Boolean ops
    ast.And,
    ast.Or,
    ast.Not,
    # Arithmetic ops
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    # Comparison ops
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
    # Collections (read-only)
    ast.List,
    ast.Tuple,
    ast.Set,
    # Calls – only whitelisted function names allowed
    ast.Call,
    ast.Attribute,
    ast.Subscript,
    ast.Index,
    ast.Slice,
    # Ternary / IfExp
    ast.IfExp,
}

# Whitelisted built-in/helper function names callable inside expressions
_ALLOWED_CALL_NAMES = frozenset(
    {
        # Date helpers exposed by the evaluator
        "date_diff",
        "date_parse",
        "today",
        "years_since",
        "days_until",
        # Math builtins
        "abs",
        "min",
        "max",
        "round",
        "len",
        "int",
        "float",
        "str",
        "bool",
    }
)

_MAX_OPS = 200  # hard cap to prevent DoS via deeply nested ASTs

_BIN_OPS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

_CMP_OPS: dict[type[ast.cmpop], Any] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}


class SafeASTEvaluator:
    """Walk an AST expression tree and evaluate it against a facts dict.

    All attribute access, function calls, and imports are strictly blocked
    unless explicitly whitelisted.
    """

    def __init__(self) -> None:
        self._op_count = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, expression: str, facts: dict[str, Any]) -> Any:
        """Parse and evaluate *expression* with *facts* as the variable namespace.

        Raises:
            SafeEvalError: For any disallowed construct or injection attempt.
            ValueError: For syntactically invalid expressions.
        """
        try:
            tree = ast.parse(expression.strip(), mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"Invalid expression syntax: {exc}") from exc

        self._op_count = 0
        self._validate_tree(tree)
        return self._eval_node(tree.body, facts)

    # ------------------------------------------------------------------
    # Tree validation pass (whitelist check before any evaluation)
    # ------------------------------------------------------------------

    def _validate_tree(self, tree: ast.AST) -> None:
        """Reject any AST node type not in the whitelist."""
        for node in ast.walk(tree):
            if type(node) not in _ALLOWED_NODES:
                raise SafeEvalError(
                    f"Disallowed AST node type '{type(node).__name__}' "
                    f"in expression. Possible injection attempt."
                )
            # Extra check: block attribute access that might expose internals
            if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                raise SafeEvalError(
                    f"Access to private attribute '{node.attr}' is forbidden."
                )
            # Block calls to non-whitelisted names
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    if func.id not in _ALLOWED_CALL_NAMES:
                        raise SafeEvalError(
                            f"Call to '{func.id}' is not allowed. "
                            f"Allowed functions: {sorted(_ALLOWED_CALL_NAMES)}"
                        )
                elif isinstance(func, ast.Attribute):
                    raise SafeEvalError(
                        "Method calls (a.b()) are not allowed in rule logic expressions."
                    )

    # ------------------------------------------------------------------
    # Recursive evaluator
    # ------------------------------------------------------------------

    def _eval_node(self, node: ast.expr, facts: dict[str, Any]) -> Any:
        self._op_count += 1
        if self._op_count > _MAX_OPS:
            raise EvalTimeout(
                f"Expression exceeded maximum operation limit ({_MAX_OPS}). "
                "Possible DoS attempt or overly complex rule."
            )

        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            name = node.id
            if name in ("True", "False", "None"):
                return {"True": True, "False": False, "None": None}[name]
            if name not in facts:
                raise SafeEvalError(
                    f"Undefined variable '{name}'. "
                    f"Available facts: {sorted(facts.keys())}"
                )
            return facts[name]

        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result = True
                for v in node.values:
                    result = result and self._eval_node(v, facts)
                return result
            if isinstance(node.op, ast.Or):
                result = False
                for v in node.values:
                    result = result or self._eval_node(v, facts)
                return result

        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, facts)
            if isinstance(node.op, ast.Not):
                return not operand
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.UAdd):
                return +operand

        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, facts)
            right = self._eval_node(node.right, facts)
            op_fn = _BIN_OPS.get(type(node.op))
            if op_fn is None:
                raise SafeEvalError(f"Unsupported binary operator: {type(node.op).__name__}")
            return op_fn(left, right)

        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, facts)
            result = True
            for op, comparator in zip(node.ops, node.comparators, strict=False):
                right = self._eval_node(comparator, facts)
                result = result and self._apply_cmp(op, left, right)
                left = right
            return result

        if isinstance(node, ast.IfExp):
            test = self._eval_node(node.test, facts)
            return self._eval_node(node.body if test else node.orelse, facts)

        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            elements = [self._eval_node(e, facts) for e in node.elts]
            if isinstance(node, ast.Set):
                return set(elements)
            if isinstance(node, ast.Tuple):
                return tuple(elements)
            return elements

        if isinstance(node, ast.Subscript):
            obj = self._eval_node(node.value, facts)
            idx = self._eval_node(node.slice, facts)
            return obj[idx]

        if isinstance(node, ast.Call):
            func_name: str = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            args = [self._eval_node(a, facts) for a in node.args]
            return self._call_builtin(func_name, args, facts)

        raise SafeEvalError(
            f"Unexpected AST node type '{type(node).__name__}' during evaluation."
        )

    # ------------------------------------------------------------------
    # Comparison helper
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_cmp(op: ast.cmpop, left: Any, right: Any) -> bool:
        fn = _CMP_OPS.get(type(op))
        if fn is None:
            raise SafeEvalError(f"Unsupported comparison operator: {type(op).__name__}")
        return bool(fn(left, right))

    # ------------------------------------------------------------------
    # Whitelisted built-in function dispatcher
    # ------------------------------------------------------------------

    @staticmethod
    def _call_builtin(name: str, args: list[Any], _facts: dict[str, Any]) -> Any:
        """Dispatch to whitelisted helper functions only."""
        if name == "abs":
            return abs(args[0])
        if name == "min":
            return min(*args)
        if name == "max":
            return max(*args)
        if name == "round":
            return round(*args)
        if name == "len":
            return len(args[0])
        if name == "int":
            return int(args[0])
        if name == "float":
            return float(args[0])
        if name == "str":
            return str(args[0])
        if name == "bool":
            return bool(args[0])
        if name == "today":
            return date.today()
        if name == "date_parse":
            # date_parse("YYYY-MM-DD")
            return datetime.strptime(str(args[0]), "%Y-%m-%d").date()
        if name == "date_diff":
            # date_diff(date_field, ref_date_str, 'days'|'years')
            # args: [date_value, ref_date, unit]
            d1 = args[0]
            d2 = args[1]
            if isinstance(d1, str):
                d1 = datetime.strptime(d1, "%Y-%m-%d").date()
            if isinstance(d2, str):
                d2 = datetime.strptime(d2, "%Y-%m-%d").date()
            unit = args[2] if len(args) > 2 else "days"
            delta = d2 - d1
            if unit == "days":
                return delta.days
            if unit == "years":
                return delta.days / 365.25
            raise SafeEvalError(f"Unknown date_diff unit: {unit!r}. Use 'days' or 'years'.")
        if name == "years_since":
            # years_since(date_str) → float years from date_str to today
            d = args[0]
            if isinstance(d, str):
                d = datetime.strptime(d, "%Y-%m-%d").date()
            return (date.today() - d).days / 365.25
        if name == "days_until":
            # days_until(date_str) → int days from today to date_str
            d = args[0]
            if isinstance(d, str):
                d = datetime.strptime(d, "%Y-%m-%d").date()
            return (d - date.today()).days

        raise SafeEvalError(
            f"Function '{name}' not in whitelist. "
            f"Allowed: {sorted(_ALLOWED_CALL_NAMES)}"
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

safe_evaluator = SafeASTEvaluator()
