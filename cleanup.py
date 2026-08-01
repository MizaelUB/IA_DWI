with open('missing.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
# omit last line if it's the guest decorator
if '@router.post("/api/auth/guest")' in lines[-1] or '@router.post("/api/auth/guest")' in lines[-2]:
    while '@router.post("/api/auth/guest")' in lines[-1]:
        lines = lines[:-1]
with open('missing_clean.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
