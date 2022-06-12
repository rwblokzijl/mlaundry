def get_last_used_profile():
    import json
    filepath = Path("~/.config/BraveSoftware/Brave-Browser/Local State").expanduser()
    with open(filepath, "r") as f:
        local_state = json.load(f)
    return local_state["profile"]["last_used"]

def encode_cookie(cookie):
    "Pads up to the nearest 16 bytes, padding should be a n long string of n's where n is the number of bytes to pad"
    encode = cookie.encode('utf8')
    remainder = len(encode) % 16
    to_pad = 16 - remainder
    return encode + (to_pad.to_bytes(1, 'big')*to_pad)

def decode_cookie(cookie):
    return cookie[:-cookie[-1]].decode('utf8')

def decrypt_cookie(encrypted_value):
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    encrypted_value = encrypted_value[3:] # trim 'v10'
    my_pass = "peanuts"
    iterations = 1
    key = PBKDF2(
        my_pass.encode('utf8'),
        b'saltysalt',
        16,
        iterations
    )
    cipher = AES.new(key, AES.MODE_CBC, IV=(b' ' * 16))
    decrypted_value = cipher.decrypt(encrypted_value)
    return decode_cookie(decrypted_value)

def encrypt_cookie(value):
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    encoded_value = encode_cookie(value)
    my_pass = "peanuts"
    iterations = 1
    key = PBKDF2(
        my_pass.encode('utf8'),
        b'saltysalt',
        16,
        iterations
    )
    cipher = AES.new(key, AES.MODE_CBC, IV=(b' ' * 16))
    assert len(encoded_value) %16 == 0
    encrypted_value = cipher.encrypt(encoded_value)
    return b'v10' + encrypted_value

def get_cookie_from_brave(host_key, name):
    import sqlite3
    last_used_profile = get_last_used_profile()
    dbfile = Path(f"~/.config/BraveSoftware/Brave-Browser/{last_used_profile}/Cookies").expanduser()
    con = sqlite3.connect(f'file:{dbfile}?mode=ro', uri=True)
    cur = con.cursor()
    PHPSESSID_enc = [a for a in cur.execute(f"SELECT encrypted_value FROM cookies WHERE host_key = '{host_key}' AND name = '{name}'")][0][0]
    PHPSESSID = decrypt_cookie(PHPSESSID_enc)
    con.close()
    return PHPSESSID

def set_cookie_in_brave(host_key, name, encrypted_value, path="/"):
    import sqlite3
    import binascii
    last_used_profile = get_last_used_profile()
    dbfile = Path(f"~/.config/BraveSoftware/Brave-Browser/{last_used_profile}/Cookies").expanduser()
    con = sqlite3.connect(f'file:{dbfile}', uri=True)
    cur = con.cursor()
    date = datetime.datetime(1601, 1, 1, 0, 0, 0) + datetime.timedelta(seconds = 129893678626216000/1e7)
    TODO = None
    creation_utc = to_win32_epoch(datetime.datetime.now())
    enc_hex = binascii.hexlify(encrypted_value).decode("utf8")
    query_data = {
        "creation_utc":       creation_utc,    # INTEGER
        "host_key":           f'"{host_key}"', # TEXT
        "top_frame_site_key": '""',            # TEXT
        "name":               f'"{name}"',     # TEXT
        "value":              '""',            # TEXT
        "encrypted_value":    f"X'{enc_hex}'", # BLOB
        "path":               f'"{path}"',     # TEXT
        "expires_utc":        0,               # INTEGER
        "is_secure":          1,               # INTEGER
        "is_httponly":        1,               # INTEGER
        "last_access_utc":    creation_utc,    # INTEGER
        "has_expires":        0,               # INTEGER
        "is_persistent":      0,               # INTEGER
        "priority":           1,               # INTEGER
        "samesite":           -1,              # INTEGER
        "source_scheme":      2,               # INTEGER
        "source_port":        443,             # INTEGER
        "is_same_party":      0                # INTEGER
    }
    values = tuple([str(x) for x in query_data.values()])
    query = f"REPLACE INTO cookies ({','.join(query_data.keys())}) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % values
    PHPSESSID_enc = cur.execute(
        query
    )
    con.commit()
    con.close()

def to_win32_epoch(dt):
    W_EPOCH = datetime.datetime(1601, 1, 1)
    return int((dt - W_EPOCH).total_seconds()) * 1_000_000

