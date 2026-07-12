"""
Quick test script to verify registration works with new bcrypt implementation
"""
import sys
import time
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.security import get_password_hash, verify_password

def test_password_hashing():
    """Test password hashing performance and correctness"""
    test_password = "TestPassword123"
    
    print("Testing password hashing...")
    print(f"Password: {test_password}")
    
    # Test hashing speed
    start_time = time.time()
    hashed = get_password_hash(test_password)
    hash_time = time.time() - start_time
    
    print(f"Hashed in {hash_time:.4f} seconds")
    print(f"Hash: {hashed[:50]}...")
    
    # Test verification
    start_time = time.time()
    is_valid = verify_password(test_password, hashed)
    verify_time = time.time() - start_time
    
    print(f"Verified in {verify_time:.4f} seconds")
    print(f"Verification result: {is_valid}")
    
    # Test wrong password
    is_invalid = verify_password("WrongPassword123", hashed)
    print(f"Wrong password verification: {is_invalid}")
    
    if is_valid and not is_invalid:
        print("\n✓ Password hashing works correctly!")
        return True
    else:
        print("\n✗ Password hashing failed!")
        return False

if __name__ == "__main__":
    success = test_password_hashing()
    sys.exit(0 if success else 1)
