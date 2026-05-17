import os

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()

_supabase = None


def _disable_broken_local_proxy():
    proxy_vars = (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    )
    for proxy_var in proxy_vars:
        proxy_value = os.getenv(proxy_var, "")
        if proxy_value.startswith("http://127.0.0.1:9"):
            os.environ.pop(proxy_var, None)


def get_supabase():
    global _supabase
    print("hello")
    if _supabase is None:
        _disable_broken_local_proxy()

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise RuntimeError("Missing SUPABASE_URL and SUPABASE_KEY in .env")

        _supabase = create_client(url, key)

    return _supabase
