import hashlib
import secrets
import string

class LicenseManager:
    def __init__(self, db):
        self.db = db

    def generate(self):
        alphabet = string.ascii_uppercase + string.digits
        raw = "SAM-" + "-".join("".join(secrets.choice(alphabet) for _ in range(5)) for _ in range(3))
        digest = hashlib.sha256(raw.encode()).hexdigest()
        self.db.save_license(digest)
        self.db.log_event(0, "license_generate", "A license key was generated")
        return raw

    def validate(self, key):
        digest = hashlib.sha256(str(key).strip().encode()).hexdigest()
        return self.db.find_license(digest) is not None
