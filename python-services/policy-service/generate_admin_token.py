from app.core.security_middleware import create_test_token
from app.core.config import get_settings

token = create_test_token(user_id="admin-user", role="ADMIN", expires_minutes=120)
with open("admin_token.txt", "w") as f:
    f.write(token)
print(f"Token written to admin_token.txt")
