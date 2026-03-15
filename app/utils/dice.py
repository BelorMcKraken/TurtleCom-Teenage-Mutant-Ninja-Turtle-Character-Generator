from __future__ import annotations

import random
import re
from typing import List, Tuple


def roll_dice(count: int, sides: int) -> Tuple[List[int], int]:
    rolls = [random.randint(1, sides) for _ in range(count)]
    return rolls, sum(rolls)


def roll_d100() -> int:
    return random.randint(1, 100)


def eval_dice_expression(expr: str) -> Tuple[int, str]:
    raw = expr.strip()
    work = raw.replace(",", "")
    work = work.replace("×", "x")
    work = re.sub(r"\s+", " ", work).strip()
    work_math = (
        work.replace(" x ", " * ").replace(" X ", " * ").replace("x", "*")
        if " x " in work or " X " in work
        else work
    )

    roll_details: List[str] = []

    def repl(m: re.Match[str]) -> str:
        num_str = m.group(1) or "1"
        die_str = m.group(2)
        n = int(num_str)
        sides = 100 if die_str == "%" else int(die_str)
        rolls, subtotal = roll_dice(n, sides)
        roll_details.append(f"rolling {n}d{sides}... {rolls} = {subtotal}")
        return str(subtotal)

    dice_re = re.compile(r"(\d*)\s*[dD]\s*(%|\d+)")
    replaced = dice_re.sub(repl, work_math)

    math_only = re.sub(r"[A-Za-z]+", "", replaced)
    math_only = math_only.replace('"', "").replace("’", "").replace("'", "")
    math_only = re.sub(r"\s+", " ", math_only).strip()

    if not re.fullmatch(r"[0-9+\-*/(). ]+", math_only):
        raise ValueError(f"Unsupported expression: {raw}")

    total = int(eval(math_only, {"__builtins__": {}}, {}))
    detail = f"{raw} -> " + " | ".join(roll_details)
    return total, detail