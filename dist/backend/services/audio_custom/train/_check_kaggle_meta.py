"""Check Kaggle dataset metadata without credentials."""
import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://www.kaggle.com/datasets/abdallamohamed312/in-the-wild-audio-deepfake"
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        html = r.read(10000).decode("utf-8", errors="replace")
    import re
    sizes = re.findall(r"(\d+\.?\d*)\s*(GB|MB|KB)", html)
    print("Size mentions:", sizes[:5])
    # Look for license
    lic = re.findall(r"[Ll]icense.*?(\bCC\b[^<\"]*|[A-Z]{2,}[-0-9.]*)", html)
    print("License fragments:", lic[:5])
    # Look for file count
    fc = re.findall(r"(\d+)\s+[Ff]ile", html)
    print("File count mentions:", fc[:5])
except Exception as e:
    print(f"Error: {e}")
