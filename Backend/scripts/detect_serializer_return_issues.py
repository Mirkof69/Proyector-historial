import ast
from pathlib import Path

ROOT = Path(r"C:\Users\Miscar\Desktop\Nueva carpeta\historial\Backend")
TARGET_DIRS = ["controles", "partos", "embarazos", "laboratorio", "ecografias", "vacunas", "calculadoras_avanzadas", "reportes", "antecedentes"]

class ReturnVisitor(ast.NodeVisitor):
    def __init__(self):
        self.returns = []

    def visit_Return(self, node):
        self.returns.append(node)
        self.generic_visit(node)

def analyze_file(filepath):
    content = filepath.read_text(encoding="utf-8-sig", errors="ignore")
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return

    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if name is get_* or validate_*
            if not (node.name.startswith("get_") or node.name.startswith("validate_")):
                continue

            # Check return type annotation
            ret_type = None
            if isinstance(node.returns, ast.Name):
                if node.returns.id in ["str", "dict", "int"]:
                    ret_type = node.returns.id
            elif isinstance(node.returns, ast.Subscript):
                # E.g. Optional[str] or list[str] - ignore if it's Optional
                if isinstance(node.returns.value, ast.Name) and node.returns.value.id == "Optional":
                    continue

            if not ret_type:
                continue

            # Find all return statements in this function
            visitor = ReturnVisitor()
            # We only want to visit the returns of this function, not nested functions/classes
            # So we visit node.body
            for child in node.body:
                visitor.visit(child)

            # Also check if the last statement is a return
            has_last_return = False
            if node.body:
                last_stmt = node.body[-1]
                if isinstance(last_stmt, ast.Return):
                    has_last_return = True

            # Analyze the returns
            for ret_node in visitor.returns:
                # Is it returning None?
                is_none = False
                if ret_node.value is None:
                    is_none = True
                elif isinstance(ret_node.value, ast.Constant) and ret_node.value.value is None:
                    is_none = True
                elif isinstance(ret_node.value, ast.Name) and ret_node.value.id == "None":
                    is_none = True

                if is_none:
                    issues.append({
                        "type": "return_none",
                        "method": node.name,
                        "line": ret_node.lineno,
                        "col": ret_node.col_offset,
                        "ret_type": ret_type
                    })

            # Check for path without return (implicit return None if not ending with return)
            # A simple heuristic: if it has branches (if/try) but no base-level return, it might fall through
            # Let's check if there is any return statement at the end of the body
            if not has_last_return:
                # If there are conditional statements but no final return at the base level, it's an issue
                has_conditionals = any(isinstance(c, (ast.If, ast.Try, ast.For, ast.While)) for c in node.body)
                if has_conditionals:
                    issues.append({
                        "type": "missing_final_return",
                        "method": node.name,
                        "line": node.end_lineno or node.lineno,
                        "ret_type": ret_type
                    })

    if issues:
        print(f"\nFile: {filepath.relative_to(ROOT)}")
        for iss in issues:
            print(f"  [{iss['type'].upper()}] Line {iss['line']}: method '{iss['method']}' declared -> {iss['ret_type']}")

def main():
    for d in TARGET_DIRS:
        dir_path = ROOT / d
        if not dir_path.exists():
            continue
        for f in dir_path.rglob("*.py"):
            if f.name == "serializers.py" or f.name == "views.py":
                analyze_file(f)

if __name__ == "__main__":
    main()
