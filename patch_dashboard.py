import re

def patch_routes():
    with open('app/api/routes.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add imports to the top of the file
    import_statement = "from app.core.security import get_current_user, create_access_token\nfrom fastapi import Depends\n"
    if "from app.core.security import get_current_user" not in content:
        content = import_statement + content

    # 2. Patch dashboard veterinarias
    content = re.sub(
        r'def get_dashboard_veterinarias\(\):',
        r'def get_dashboard_veterinarias(token_payload: dict = Depends(get_current_user)):',
        content
    )

    # 3. Patch dashboard citas
    citas_def_old = r'def get_dashboard_citas\(veterinary_id: Optional\[int\] = None\):'
    citas_def_new = r'''def get_dashboard_citas(veterinary_id: Optional[int] = None, token_payload: dict = Depends(get_current_user)):
    if token_payload.get("type") == "guest_token" and veterinary_id is not None and token_payload.get("veterinary_id") != veterinary_id:
        raise HTTPException(status_code=403, detail="Acceso denegado a esta veterinaria")
    elif token_payload.get("type") == "auth_token" and veterinary_id is not None and token_payload.get("veterinary_id") != veterinary_id:
        # Prevent standard users from accessing other vet's data
        raise HTTPException(status_code=403, detail="Acceso denegado a esta veterinaria")
    
    # If no veterinary_id is provided, default to the token's veterinary_id to restrict them to their own data
    if veterinary_id is None:
        veterinary_id = token_payload.get("veterinary_id")'''
    content = re.sub(citas_def_old, citas_def_new, content)

    # 4. Patch dashboard mascotas
    mascotas_def_old = r'def get_dashboard_mascotas\(veterinary_id: Optional\[int\] = None\):'
    mascotas_def_new = r'''def get_dashboard_mascotas(veterinary_id: Optional[int] = None, token_payload: dict = Depends(get_current_user)):
    if veterinary_id is not None and token_payload.get("veterinary_id") != veterinary_id:
        raise HTTPException(status_code=403, detail="Acceso denegado a esta veterinaria")
    if veterinary_id is None:
        veterinary_id = token_payload.get("veterinary_id")'''
    content = re.sub(mascotas_def_old, mascotas_def_new, content)

    # 5. Patch dashboard clientes
    clientes_def_old = r'def get_dashboard_clientes\(veterinary_id: Optional\[int\] = None\):'
    clientes_def_new = r'''def get_dashboard_clientes(veterinary_id: Optional[int] = None, token_payload: dict = Depends(get_current_user)):
    if veterinary_id is not None and token_payload.get("veterinary_id") != veterinary_id:
        raise HTTPException(status_code=403, detail="Acceso denegado a esta veterinaria")
    if veterinary_id is None:
        veterinary_id = token_payload.get("veterinary_id")'''
    content = re.sub(clientes_def_old, clientes_def_new, content)

    # 6. Patch api_auth_login
    login_old = r'''            return \{
                "status": "success",
                "username": row\["username"\],
                "veterinary_id": row\["veterinary_id"\],
                "veterinary_name": row\["veterinary_name"\]
            \}'''
    login_new = r'''            access_token = create_access_token(row["veterinary_id"], 0, row["username"])
            return {
                "status": "success",
                "username": row["username"],
                "veterinary_id": row["veterinary_id"],
                "veterinary_name": row["veterinary_name"],
                "access_token": access_token
            }'''
    content = re.sub(login_old, login_new, content)

    with open('app/api/routes.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched app/api/routes.py")

patch_routes()
