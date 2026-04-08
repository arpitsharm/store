"""
Paytm Checksum Generation and Verification
Official Paytm checksum algorithm with proper salt generation
"""
import base64
import string
import random
import hashlib
from Crypto.Cipher import AES


# Paytm Payment Gateway Configuration
# =====================================

# Real Paytm Test Credentials (These work with Paytm's staging environment)
MID = "WorldP64425807474247"
MERCHANT_KEY = "bKMfNxPPf_QdZppa"
WEBSITE = "WEBSTAGING"  # For testing
INDUSTRY_TYPE_ID = "Retail"
CHANNEL_ID = "WEB"

# Paytm Gateway URLs
# For Testing/Staging:
PAYTM_HOST_URL = "https://securegw-stage.paytm.in"
# For Production (use when going live):
# PAYTM_HOST_URL = "https://securegw.paytm.in"

# Encryption constants (DO NOT CHANGE)
IV = "@@@@&&&&####$$$$"
BLOCK_SIZE = 16

# Test mode disabled - using real Paytm gateway with test credentials
TEST_MODE = False


def __id_generator__(size=6, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    """Generate random salt string"""
    return ''.join(random.choice(chars) for _ in range(size))


def __get_param_string__(params):
    """Convert params dict to sorted pipe-separated string"""
    params_string = []
    for key in sorted(params.keys()):
        if "REFUND" in params[key] or "|" in params[key]:
            raise ValueError(f"Invalid character '|' in parameter {key}")
        value = params[key]
        params_string.append('' if value == 'null' else str(value))
    return '|'.join(params_string)


def __pad__(s):
    """PKCS7 padding"""
    return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)


def __unpad__(s):
    """Remove PKCS7 padding"""
    if not s or len(s) == 0:
        return s
    try:
        return s[0:-ord(s[-1])]
    except (IndexError, TypeError, ValueError):
        # If unpadding fails, return the string as-is
        return s


def __encode__(to_encode, iv, key):
    """Encrypt and encode to base64"""
    # Pad
    to_encode = __pad__(to_encode)
    # Encrypt
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    to_encode = cipher.encrypt(to_encode.encode('utf-8'))
    # Encode to base64
    to_encode = base64.b64encode(to_encode)
    return to_encode.decode("UTF-8")


def __decode__(to_decode, iv, key):
    """Decode from base64 and decrypt"""
    # Decode from base64
    to_decode = base64.b64decode(to_decode)
    # Decrypt
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    to_decode = cipher.decrypt(to_decode)
    if type(to_decode) == bytes:
        to_decode = to_decode.decode()
    # Remove padding
    return __unpad__(to_decode)


def generate_checksum(param_dict, merchant_key, salt=None):
    """
    Generate checksum for Paytm payment request
    Official Paytm algorithm with salt
    """
    # Get parameter string (sorted and pipe-separated)
    params_string = __get_param_string__(param_dict)
    
    # Generate or use provided salt
    salt = salt if salt else __id_generator__(4)
    
    # Create final string with salt
    final_string = f'{params_string}|{salt}'
    
    # Generate SHA256 hash
    hasher = hashlib.sha256(final_string.encode())
    hash_string = hasher.hexdigest()
    
    # Append salt to hash
    hash_string += salt
    
    # Encrypt and encode
    return __encode__(hash_string, IV, merchant_key)


def verify_checksum(param_dict, merchant_key, checksum):
    """
    Verify checksum from Paytm response
    Official Paytm verification algorithm
    """
    # Remove CHECKSUMHASH from params
    if 'CHECKSUMHASH' in param_dict:
        param_dict.pop('CHECKSUMHASH')
    
    # Check if checksum is valid
    if not checksum or checksum.strip() == '':
        return False
    
    try:
        # Decode the checksum to get salt
        paytm_hash = __decode__(checksum, IV, merchant_key)
        salt = paytm_hash[-4:]
        
        # Regenerate checksum with same salt
        calculated_checksum = generate_checksum(param_dict, merchant_key, salt=salt)
        
        # Compare checksums
        return calculated_checksum == checksum
    except Exception as e:
        # If verification fails for any reason, return False
        print(f"Checksum verification error: {str(e)}")
        return False


def generate_checksum_by_str(param_str, merchant_key, salt=None):
    """Generate checksum from string (alternative method)"""
    params_string = param_str
    salt = salt if salt else __id_generator__(4)
    final_string = f'{params_string}|{salt}'
    
    hasher = hashlib.sha256(final_string.encode())
    hash_string = hasher.hexdigest()
    hash_string += salt
    
    return __encode__(hash_string, IV, merchant_key)


def verify_checksum_by_str(param_str, merchant_key, checksum):
    """Verify checksum from string (alternative method)"""
    paytm_hash = __decode__(checksum, IV, merchant_key)
    salt = paytm_hash[-4:]
    calculated_checksum = generate_checksum_by_str(param_str, merchant_key, salt=salt)
    return calculated_checksum == checksum


def get_paytm_config():
    """
    Get Paytm configuration
    """
    return {
        'MID': MID,
        'MERCHANT_KEY': MERCHANT_KEY,
        'PAYTM_HOST_URL': PAYTM_HOST_URL,
        'TXN_URL': f"{PAYTM_HOST_URL}/theia/processTransaction",
        'STATUS_URL': f"{PAYTM_HOST_URL}/order/status",
        'WEBSITE': WEBSITE,
        'INDUSTRY_TYPE_ID': INDUSTRY_TYPE_ID,
        'CHANNEL_ID': CHANNEL_ID,
    }
