import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# Get encryption key from environment variable, or use a default one for development
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'ThisIsA32ByteKeyForAES256Encryption!')
# Ensure the key is 32 bytes (256 bits) for AES-256
if len(ENCRYPTION_KEY) < 32:
    ENCRYPTION_KEY = ENCRYPTION_KEY.ljust(32, '0')
elif len(ENCRYPTION_KEY) > 32:
    ENCRYPTION_KEY = ENCRYPTION_KEY[:32]

def encrypt_data(data):
    """
    Encrypts data using AES-256 encryption.
    
    Args:
        data (str): The data to encrypt
        
    Returns:
        str: Base64 encoded encrypted data
    """
    if data is None:
        return None
    
    # Convert data to bytes if it's a string
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # Generate a random 16-byte IV
    iv = os.urandom(16)
    
    # Create an encryptor object
    cipher = Cipher(
        algorithms.AES(ENCRYPTION_KEY.encode('utf-8')),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # Pad the data to be a multiple of 16 bytes (AES block size)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    # Encrypt the padded data
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    
    # Combine IV and encrypted data and encode as base64
    result = base64.b64encode(iv + encrypted_data).decode('utf-8')
    
    return result

def decrypt_data(encrypted_data):
    """
    Decrypts data that was encrypted using AES-256 encryption.
    
    Args:
        encrypted_data (str): Base64 encoded encrypted data
        
    Returns:
        str: Decrypted data as a string
    """
    if encrypted_data is None:
        return None
    
    try:
        # Decode the base64 encoded string
        data = base64.b64decode(encrypted_data)
        
        # Extract the IV and ciphertext
        iv = data[:16]
        ciphertext = data[16:]
        
        # Create a decryptor object
        cipher = Cipher(
            algorithms.AES(ENCRYPTION_KEY.encode('utf-8')),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt the ciphertext
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad the decrypted data
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        # Convert bytes to string
        return data.decode('utf-8')
    except Exception as e:
        print(f"Error decrypting data: {str(e)}")
        return None
