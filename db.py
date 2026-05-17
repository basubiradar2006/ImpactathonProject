import os

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()

_supabase = None


def get_supabase():
    global _supabase

    if _supabase is None:
        # url = os.getenv("SUPABASE_URL")
        # key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        url = "https://dckzggsaoecqohcjmkho.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRja3pnZ3Nhb2VjcW9oY2pta2hvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg5Mjc2NzMsImV4cCI6MjA5NDUwMzY3M30.DFH9IQRY_2Dv4sSo5T2OGGwY-Soy2WjYHxIwTUXJ2pc"
        print(url)
        print(key[:20])
        if not url or not key:
            raise RuntimeError("Missing SUPABASE_URL and SUPABASE_KEY in .env")

        _supabase = create_client(url, key)

    return _supabase
