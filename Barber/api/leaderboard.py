from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(__file__))
from _kv import zrevrange_withscores


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            query = parse_qs(urlparse(self.path).query)
            limit = min(int(query.get("limit", ["5"])[0]), 100)

            raw = zrevrange_withscores("leaderboard", 0, limit - 1)
            # raw is [member1, score1, member2, score2, ...]
            entries = []
            for i in range(0, len(raw), 2):
                member = json.loads(raw[i])
                entries.append({
                    "player_name": member["n"],
                    "score": int(raw[i + 1]),
                    "created_at": member.get("t", ""),
                })

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(entries).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
