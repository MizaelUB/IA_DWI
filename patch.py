with open('app/api/routes.py', 'r', encoding='utf-8') as f:
    routes_content = f.read()

with open('missing_clean.py', 'r', encoding='utf-8') as f:
    missing_content = f.read()

# I will replace the auth comment header with missing_content + the auth comment header (since missing_content has it)
# Let's find exactly where to insert.
target = "# Endpoints de Autenticación\n# ============================================================\nfrom pydantic import BaseModel"

if target in routes_content:
    new_content = routes_content.replace(target, missing_content)
    with open('app/api/routes.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced successfully")
else:
    print("Target not found. Doing manual splice.")
    # Fallback to lines 1330
    lines = routes_content.split('\n')
    lines = lines[:1329] + missing_content.split('\n') + lines[1332:]
    with open('app/api/routes.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print("Spliced by line numbers")
