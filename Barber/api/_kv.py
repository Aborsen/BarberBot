"""
Upstash Redis helper using only the standard library.
Env vars are auto-set by Vercel when you connect Upstash from the marketplace.
"""
import urllib.request
import json
import os


def _get_url_and_token():
    # Support both Vercel KV (legacy) and Upstash marketplace env var names
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    if not url or not token:
        raise RuntimeError("Missing Redis env vars: UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN")
    return url, token


def _pipeline(*commands):
    """Execute one or more Redis commands via the Upstash REST pipeline endpoint."""
    url, token = _get_url_and_token()
    endpoint = url.rstrip("/") + "/pipeline"
    data = json.dumps(list(commands)).encode()
    req = urllib.request.Request(endpoint, data=data, method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def zadd(key, score, member_str):
    result = _pipeline(["ZADD", key, score, member_str])
    return result[0]["result"]


def zrevrange_withscores(key, start, stop):
    """Returns flat list: [member1, score1, member2, score2, ...]"""
    result = _pipeline(["ZREVRANGE", key, start, stop, "WITHSCORES"])
    return result[0]["result"]
