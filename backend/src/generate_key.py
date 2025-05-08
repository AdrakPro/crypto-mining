# Only for generating keys (this password is not for production)
from security import get_password_hash
import hashlib

password = "haslo"
sha256_hash = hashlib.sha256(password.encode()).hexdigest()
bcrypt_hash = get_password_hash(sha256_hash)
print(bcrypt_hash)  # Put this in .env as ADMIN_PASSWORD
