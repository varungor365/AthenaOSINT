"""
Stub Generator.
Run this once to generate placeholder module files for all tools in valid registry
that don't exist yet.
"""
from pathlib import Path
from modules.registry import MODULE_REGISTRY

def generate_stubs():
    base_dir = Path(__file__).parent
    
    template = """
\"\"\"
{name} Module (Stub).
{desc}
\"\"\"
from core.engine import Profile

META = {{
    'description': '{desc}',
    'target_type': '{type}'
}}

def scan(target: str, profile: Profile) -> None:
    # This is a stub. Implement logic here.
    pass
"""

    for name, info in MODULE_REGISTRY.items():
        file_path = base_dir / f"{name}.py"
        if not file_path.exists():
            print(f"Creating stub: {name}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template.format(
                    name=name.title(),
                    desc=info['desc'],
                    type=info['type']
                ))

if __name__ == "__main__":
    generate_stubs()
