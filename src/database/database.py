import os
from supabase_py import create_client, Client


class Supabase:
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")
    client: Client

    def __init__(self):
        self.client = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)
