
import re

with open('test_modules.py', 'r') as f:
    content = f.read()

# Fix instantiation
content = re.sub(
    r'engine = AthenaEngine\(\)',
    'engine = AthenaEngine(target_query=target, target_type=target_type)',
    content
)

# Fix run_scan call
# We need to replace the call that spans multiple lines.
# Pattern matches: result = engine.run_scan( ... )
pattern = r'result = engine\.run_scan\(\s*target=target,\s*target_type=target_type,\s*modules=\[module_name\],\s*max_depth=1\s*\)'
replacement = 'result = engine.run_scan([module_name])'
# Note: The regex needs to handle the newlines/indentation.
# A simpler way is to just write the specific function `test_module` logic fresh.

# More robust regex for the specific block
content = re.sub(
    r'engine\.run_scan\s*\(\s*target=target,\s*target_type=target_type,\s*modules=\[module_name\],\s*max_depth=1\s*\)',
    'engine.run_scan([module_name])',
    content,
    flags=re.DOTALL
)

with open('test_modules.py', 'w') as f:
    f.write(content)

print("Patched test_modules.py")
