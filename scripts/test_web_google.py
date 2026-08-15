import urllib.request
import json

def main():
    url = "http://127.0.0.1:5000/api/research"
    payload = json.dumps({"ticker": "GOOGLE", "task": "Analyze Alphabet GOOGL revenue"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("Status:", res.get("status"))
        print("Error Message:", res.get("message"))
        print("Ticker:", res.get("ticker"))

if __name__ == "__main__":
    main()
