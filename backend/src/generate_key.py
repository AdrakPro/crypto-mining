from security import get_password_hash
import hashlib

password = "8349dfk935829fkdk!sk"
sha256_hash = hashlib.sha256(password.encode()).hexdigest()
bcrypt_hash = get_password_hash(sha256_hash)
print(bcrypt_hash)  # Put this in .env as ADMIN_PASSWORD
