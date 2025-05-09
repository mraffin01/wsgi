from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# Step 1: Generate RSA keys (private and public)
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Save the private and public keys to files
    with open("../config/private_key.pem", "wb") as private_file:
        private_file.write(private_pem)

    with open("../config/public_key.pem", "wb") as public_file:
        public_file.write(public_pem)

# Step 2: Encrypt the password with the public key
def encrypt_password(password, public_key_path="../config/public_key.pem"):
    with open(public_key_path, "rb") as public_file:
        public_key = serialization.load_pem_public_key(public_file.read(), backend=default_backend())

    encrypted_password = public_key.encrypt(
        password.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    with open(".userfile", "wb") as file:
        file.write(encrypted_password)

# Step 3: Decrypt the password with the private key
def decrypt_password(private_key_path="../config/private_key.pem", file_path=".userfile"):
    with open(private_key_path, "rb") as private_file:
        private_key = serialization.load_pem_private_key(private_file.read(), password=None, backend=default_backend())

    with open(file_path, "rb") as file:
        encrypted_password = file.read()

    decrypted_password = private_key.decrypt(
        encrypted_password,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return decrypted_password.decode()

# Example usage
# Generate RSA keys (only once)
#generate_rsa_keys()

# Encrypt password and store it
password_to_store = "[6h!E$uWkMebM/V-=3U7OmQ1V"
encrypt_password(password_to_store)

# Decrypt the password
decrypted_password = decrypt_password()
print(f"Decrypted password: {decrypted_password}")

