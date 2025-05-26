import hashlib
import bcrypt

# Step 1: Original password
password = "haslo"

# Step 2: Hash it with SHA-256
sha256_hash = hashlib.sha256(password.encode()).hexdigest()

# Step 3: Hash the SHA-256 hex digest with bcrypt
bcrypt_hash = bcrypt.hashpw(sha256_hash.encode(), bcrypt.gensalt())

# Step 4: Print the bcrypt hash
print(bcrypt_hash.decode())  # Put this in .env as ADMIN_PASSWOR
