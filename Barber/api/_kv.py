"""
Vercel KV (Upstash Redis) helper using only the standard library.
Env vars KV_REST_API_URL and KV_REST_API_TOKEN are auto-set by Vercel
when you connect a KV store from the project dashboard.
"""
import urllib.request
import json
import os


def _pipeline(*commands):
    """Execute one or more Redis commands via the Upstash REST pipeline endpoint."""
    url = os.environ["KV_REST_API_URL"].rstrip("/") + "/pipeline"
    data = json.dumps(list(commands)).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", "Bearer " + os.environ["KV_REST_API_TOKEN"])
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
