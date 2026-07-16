#!/usr/bin/env python3
"""
fix_serializer_implicit_returns.py - Agrega retornos por defecto en métodos de serializers
que tienen anotación de tipo pero carecen de una sentencia return al final.
"""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\Miscar\Desktop\Nueva carpeta\historial\Backend")
TARGET_DIRS = ["controles", "partos", "embarazos", "laboratorio", "ecografias", "vacunas", "calculadoras_avanzadas"]

def read_file(path):
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")

def fix_file(filepath):
    content = read_file(filepath)
    lines = content.split("\n")
    result = []
    i = 0
    changed = False

    while i < len(lines):
        line = lines[i]
        # Buscar definiciones de metodos get_* o validate_* con -> str, -> dict, o -> int
        m = re.match(r"^(\s+)def (get_\w+|validate_\w+)\(self,.*\)\s*->\s*(str|dict|int)\s*:$", line)
        if m:
            indent = m.group(1)
            method_name = m.group(2)
            ret_type = m.group(3)
            body_indent = indent + "    "

            # Recoger las lineas del metodo
            body = [line]
            j = i + 1
            while j < len(lines):
                nl = lines[j]
                stripped = nl.strip()
                if stripped == "":
                    body.append(nl)
                    j += 1
                    continue
                cur_indent = len(nl) - len(nl.lstrip())
                if cur_indent <= len(indent) and stripped:
                    break
                body.append(nl)
                j += 1

            # Analizar el cuerpo del metodo
            # Si hay un return a nivel de body_indent, asumimos que esta cubierto
            has_base_return = False
            for bl in body[1:]:
                # Debe empezar exactamente con el nivel de indentacion del cuerpo y ser "return"
                if bl.startswith(body_indent + "return ") or bl.startswith(body_indent + "return\n") or bl.strip() == "return":
                    has_base_return = True
                    break

            if not has_base_return:
                # Agregar return al final del cuerpo (pero antes de lineas vacias finales si las hay)
                insert_pos = len(body)
                while insert_pos > 1 and body[insert_pos - 1].strip() == "":
                    insert_pos -= 1

                default_val = '""' if ret_type == "str" else ("{}" if ret_type == "dict" else "0")
                body.insert(insert_pos, f"{body_indent}return {default_val}")
                changed = True
                print(f"  [FIXED] {filepath.relative_to(ROOT)}:{i+1} - Added return {default_val} to {method_name}")

            result.extend(body)
            i = j
        else:
            result.append(line)
            i += 1

    if changed:
        filepath.write_text("\n".join(result), encoding="utf-8")
        return True
    return False

def main():
    print("=" * 60)
    print("  FIX SERIALIZER IMPLICIT RETURNS")
    print("=" * 60)

    fixed_count = 0
    for d in TARGET_DIRS:
        dir_path = ROOT / d
        if not dir_path.exists():
            print(f"[SKIP] Directory {d} does not exist")
            continue

        for f in dir_path.rglob("serializers.py"):
            print(f"Scanning: {f.relative_to(ROOT)}")
            if fix_file(f):
                fixed_count += 1

    print(f"\n[DONE] Modified {fixed_count} files.")

if __name__ == "__main__":
    main()
