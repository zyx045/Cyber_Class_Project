import os
from cryptography.fernet import Fernet
import base64
import json
import hashlib

class Encrypter:
    def __init__(self, password: str):
        """
        Initialize the encrypter with a password.
        The password is used to derive a key for encryption/decryption.
        """
        self.password = password
        # Derive a 32-byte key from the password using SHA-256
        key = hashlib.sha256(password.encode()).digest()
        # Convert to URL-safe base64-encoded bytes
        self.fernet_key = base64.urlsafe_b64encode(key)
        self.fernet = Fernet(self.fernet_key)
        self.START_MARKER = b"STEGO_ENC_START"
        self.END_MARKER = b"STEGO_ENC_END"
    
    def encrypt_data(self, data: dict) -> bytes:
        """
        Encrypt the data dictionary into a binary format with markers.
        """
        # Convert dictionary to JSON string then to bytes
        json_data = json.dumps(data).encode('utf-8')
        # Encrypt the data
        encrypted = self.fernet.encrypt(json_data)
        # Add markers and return
        return self.START_MARKER + encrypted + self.END_MARKER
    
    def decrypt_data(self, encrypted_data: bytes) -> dict:
        """
        Decrypt the binary data back to a dictionary.
        """
        # Find the markers
        start_idx = encrypted_data.find(self.START_MARKER)
        if start_idx == -1:
            raise ValueError("Start marker not found in encrypted data")
            
        end_idx = encrypted_data.find(self.END_MARKER, start_idx)
        if end_idx == -1:
            raise ValueError("End marker not found in encrypted data")
            
        # Extract the encrypted data between markers
        encrypted = encrypted_data[start_idx + len(self.START_MARKER):end_idx]
        
        # Decrypt and parse JSON
        try:
            decrypted = self.fernet.decrypt(encrypted)
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode('utf-8')
