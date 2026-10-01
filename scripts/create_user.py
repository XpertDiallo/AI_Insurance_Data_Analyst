from __future__ import annotations
import argparse, json
from pathlib import Path
import bcrypt

p=argparse.ArgumentParser(); p.add_argument("username"); p.add_argument("--role", default="admin"); p.add_argument("--password", required=True); p.add_argument("--file", default="data/users.json")
a=p.parse_args(); path=Path(a.file); path.parent.mkdir(parents=True,exist_ok=True)
data=json.loads(path.read_text()) if path.exists() else {"users":[]}
data["users"]=[u for u in data.get("users",[]) if u.get("username")!=a.username]
data["users"].append({"username":a.username,"display_name":a.username,"role":a.role,"active":True,"password_hash":bcrypt.hashpw(a.password.encode(),bcrypt.gensalt()).decode()})
path.write_text(json.dumps(data,indent=2),encoding="utf-8"); print(f"Utilisateur {a.username} enregistré dans {path}")
