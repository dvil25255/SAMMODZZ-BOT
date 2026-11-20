from supabase import create_client

class Database:
    def __init__(self, settings):
        if not settings.supabase_url or not settings.supabase_key:
            raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.")
        self.client = create_client(settings.supabase_url, settings.supabase_key)

    def add_file(self, record):
        self.client.table("bot_files").insert(record).execute()

    def list_files(self, limit=30):
        res = self.client.table("bot_files").select("*").order("created_at", desc=True).limit(limit).execute()
        return res.data or []

    def get_file(self, file_id):
        res = self.client.table("bot_files").select("*").eq("id", file_id).limit(1).execute()
        return (res.data or [None])[0]

    def delete_file_record(self, file_id):
        self.client.table("bot_files").delete().eq("id", file_id).execute()

    def log_event(self, actor_id, action, details):
        self.client.table("bot_activity").insert({
            "actor_id": int(actor_id), "action": str(action)[:80], "details": str(details)[:500]
        }).execute()

    def activity_count(self):
        res = self.client.table("bot_activity").select("id", count="exact").execute()
        return res.count or 0

    def file_count(self):
        res = self.client.table("bot_files").select("id", count="exact").execute()
        return res.count or 0

    def save_license(self, key_hash):
        self.client.table("bot_licenses").insert({"key_hash": key_hash, "is_active": True}).execute()

    def find_license(self, key_hash):
        res = self.client.table("bot_licenses").select("*").eq("key_hash", key_hash).eq("is_active", True).limit(1).execute()
        return (res.data or [None])[0]
