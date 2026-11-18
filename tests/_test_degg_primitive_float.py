"""Функциональный тест DeggPrimitiveFloat (Python) — без ComfyUI, без torch.

Нода — примитив: одно поле FLOAT, выход = вход. Тест держит не «сколько строк
в файле», а контракт, на который опираются workflow:
  • тип/границы поля (workflow, сохранённый со значением вне min..max, не должен
    отвергаться при загрузке, поэтому границы — ±sys.float_info.max, а не 0..1);
  • значение проходит насквозь без округления и без потери знака/нуля;
  • имена для меню и REGISTRY-ключ не переименованы (переименование ломает
    сохранённые workflow молча: ComfyUI ищет класс по имени).

Запуск:  cd Degg_Primitive_float && python tests/_test_degg_primitive_float.py
"""

import importlib.util
import sys
from pathlib import Path

NODE = Path(__file__).resolve().parent.parent / "degg_primitive_float.py"

fails = []
oks = []


def _p(text):
    """Печать, безопасная для cp1251 (в консоли Windows иначе падает)."""
    try:
        enc = sys.stdout.encoding or "utf-8"
        sys.stdout.write(str(text).encode(enc, "replace").decode(enc, "replace") + "\n")
    except Exception:
        pass


def check(name, cond, extra=""):
    (oks if cond else fails).append(name)
    _p(("  ok  " if cond else "  FAIL") + f"  {name}" + (f"  [{extra}]" if extra and not cond else ""))


spec = importlib.util.spec_from_file_location("degg_primitive_float", NODE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

Cls = mod.NODE_CLASS_MAPPINGS["DeggPrimitiveFloat"]
it = Cls.INPUT_TYPES()

# ────────────────────────────── контракт входа ──────────────────────────────
check("INPUT_TYPES: поле «float» обязательное",
      list(it.get("required", {})) == ["float"], list(it.get("required", {})))

kind, opts = it["required"]["float"]
check("INPUT_TYPES: тип поля FLOAT", kind == "FLOAT", kind)
check("INPUT_TYPES: default = 1.0", opts.get("default") == 1.0, opts.get("default"))
check("INPUT_TYPES: step = 0.01", opts.get("step") == 0.01, opts.get("step"))
check("INPUT_TYPES: границы ±sys.float_info.max (значение из workflow не отвергается)",
      opts.get("min") == -sys.float_info.max and opts.get("max") == sys.float_info.max,
      (opts.get("min"), opts.get("max")))

# ─────────────────────────────── проход значения ────────────────────────────
node = Cls()
check("process(): возвращает кортеж из одного элемента", isinstance(node.process(2.5), tuple))
check("process(): значение насквозь (2.5)", node.process(2.5) == (2.5,), node.process(2.5))
check("process(): ноль не превращается в default", node.process(0.0) == (0.0,), node.process(0.0))
check("process(): отрицательное значение сохраняет знак",
      node.process(-3.75) == (-3.75,), node.process(-3.75))
check("process(): целое число не округляется до int-представления",
      node.process(7) == (7,) and isinstance(node.process(7)[0], int), node.process(7))
check("process(): экстремум float проходит без переполнения",
      node.process(1.7976931348623157e308) == (1.7976931348623157e308,))
check("process(): без аргумента отдаёт default 1.0", node.process() == (1.0,), node.process())

# ─────────────────────────── метаданные класса/меню ────────────────────────
check("RETURN_TYPES = (FLOAT,)", Cls.RETURN_TYPES == ("FLOAT",), Cls.RETURN_TYPES)
check("RETURN_NAMES = (float,)", Cls.RETURN_NAMES == ("float",), Cls.RETURN_NAMES)
check("FUNCTION = process (ComfyUI зовёт именно этот метод)", Cls.FUNCTION == "process", Cls.FUNCTION)
check("CATEGORY = My_custom_nodes", Cls.CATEGORY == "My_custom_nodes", Cls.CATEGORY)
check("REGISTRY-ключ не переименован",
      mod.NODE_CLASS_MAPPINGS == {"DeggPrimitiveFloat": Cls}, list(mod.NODE_CLASS_MAPPINGS))
check("имя в меню на месте",
      mod.NODE_DISPLAY_NAME_MAPPINGS.get("DeggPrimitiveFloat") == "Degg Primitive float",
      mod.NODE_DISPLAY_NAME_MAPPINGS)

_p("")
_p(f"PASS: {len(oks)}  FAIL: {len(fails)}")
if fails:
    _p("failed: " + ", ".join(fails))
else:
    _p("ТЕСТ ПРОЙДЕН")
sys.exit(1 if fails else 0)
