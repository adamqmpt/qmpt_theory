"""
Tiny expression evaluator for derived metrics.
Supports basic arithmetic on existing metric keys.
"""

from __future__ import annotations

import ast
from typing import Dict, Any


class _SafeEval(ast.NodeVisitor):
    allowed_nodes = {
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.Num,
        ast.Constant,
        ast.Load,
        ast.Name,
        ast.USub,
        ast.UAdd,
        ast.Call,
    }
    allowed_funcs = {"abs": abs, "max": max, "min": min}

    def __init__(self, variables: Dict[str, Any]):
        self.vars = variables

    def visit(self, node):
        if type(node) not in self.allowed_nodes:
            raise ValueError(f"Illegal expression element: {type(node).__name__}")
        return super().visit(node)

    def visit_Name(self, node):
        if node.id in self.vars:
            return self.vars[node.id]
        raise ValueError(f"Unknown variable {node.id}")

    def visit_Constant(self, node):
        return node.value

    def visit_Num(self, node):
        return node.n

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError("Unsupported unary operator")

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left ** right
        if isinstance(node.op, ast.Mod):
            return left % right
        raise ValueError("Unsupported binary operator")

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in self.allowed_funcs:
            func = self.allowed_funcs[node.func.id]
            args = [self.visit(a) for a in node.args]
            return func(*args)
        raise ValueError("Unsupported function call")


def evaluate_derived(metrics: Dict[str, Any], expressions: Dict[str, str]) -> Dict[str, Any]:
    derived: Dict[str, Any] = {}
    for name, expr in expressions.items():
        try:
            tree = ast.parse(expr, mode="eval")
            val = _SafeEval(metrics).visit(tree.body)
            derived[name] = val
        except Exception:
            continue
    return derived
