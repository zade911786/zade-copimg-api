import sys
import json
import time
import os
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler

try:
    import cloudscraper
except ImportError:
    cloudscraper = None

TMP_DIR = "/tmp/aifree_cache"

class handler(BaseHTTPRequestHandler):

    def _json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Powered-By", "Zade-AI-Free-Forever-Engine")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=4).encode("utf-8"))

    def do_OPTIONS(self):
        self._json(200, {})

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed_url.query)

        # ── Route 1: Serve Cached/Downloaded Media ──────────────────
        if "file" in qs:
            filename = os.path.basename(qs["file"][0].strip())
            file_path = os.path.join(TMP_DIR, filename)
            
            if os.path.exists(file_path):
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.end_headers()
                    with open(file_path, "rb") as f:
                        self.wfile.write(f.read())
                    return
                except Exception as serve_err:
                    self._json(500, {"success": False, "message": str(serve_err)})
                    return
            else:
                self._json(404, {"success": False, "message": "File expired or not found on proxy server."})
                return

        # ── Route 2: Reverse Engineered Image Pipeline ──────────────
        if cloudscraper is None:
            self._json(500, {"success": False, "message": "cloudscraper library missing in backend environment."})
            return

        prompt = qs.get("prompt", [""])[0].strip()
        if not prompt:
            self._json(400, {"success": False, "message": "prompt query parameter is required."})
            return

        host = self.headers.get("Host", "zade-copimg-api.vercel.app")
        base_url = f"https://{host}{parsed_url.path}"

        start_time = time.time()
        try:
            os.makedirs(TMP_DIR, exist_ok=True)

            # Cloudflare-bypassing scraper session initialized
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'android', # Logs ke mutabik unka system mobile user agents ko respect kar raha hai
                    'mobile': True
                }
            )

            # Exact base domain matching your logs
            base_target = "https://aifreeforever.com"
            
            # Step 1: Hit `/api/enhance-prompt` as documented in your uploaded .md file
            enhance_url = f"{base_target}/api/enhance-prompt"
            enhance_headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Android 13; Mobile; rv:128.0) Gecko/128.0 Firefox/128.0",
                "Referer": f"{base_target}/image-generators?timestamp={int(time.time()*1000)}"
            }
            
            enhance_payload = {"prompt": prompt}
            
            enhance_res = scraper.post(enhance_url, headers=enhance_headers, json=enhance_payload, timeout=15)
            
            # Fallback checking if enhance fails, use normal prompt
            target_prompt = prompt
            if enhance_res.status_code == 200:
                try:
                    enhance_data = enhance_res.json()
                    if enhance_data.get("success") and enhance_data.get("enhancedPrompt"):
                        target_prompt = enhance_data["enhancedPrompt"]
                except Exception:
                    pass

            # Step 2: Hit `/api/v2/generate-image`
            gen_url = f"{base_target}/api/v2/generate-image"
            gen_payload = {
                "prompt": target_prompt,
                "model": "flux-2-pro",  # From page metadata: defaults to Flux 2 Pro/Z-Image Turbo
                "aspectRatio": "1:1",
                "numImages": 1
            }

            gen_res = scraper.post(gen_url, headers=enhance_headers, json=gen_payload, timeout=35)

            if gen_res.status_code != 200:
                self._json(gen_res.status_code, {
                    "success": False,
                    "code": "CF_OR_UPSTREAM_REJECTION",
                    "message": f"Server responded with status {gen_res.status_code}",
                    "debug_html_snippet": gen_res.text[:300]
                })
                return

            # Parsing structural response matching your logs stream/JSON nodes
            try:
                res_data = gen_res.json()
            except Exception:
                # Agar chunk data format streams mein backfire kare toh response filter handling
                self._json(502, {
                    "success": False, 
                    "message": "Raw stream parsing required or unexpected token.",
                    "raw": gen_res.text[:1000]
                })
                return

            # Link Extraction Logic
            cdn_urls = []
            if "images" in res_data:
                for img in res_data["images"]:
                    url = img.get("url") or img.get("contentUrl") or img.get("src")
                    if url: cdn_urls.append(url)
            elif "data" in res_data:
                # Handling nested dynamic array mapping
                if isinstance(res_data["data"], list):
                    for item in res_data["data"]:
                        url = item.get("url") or item.get("image")
                        if url: cdn_urls.append(url)
                elif isinstance(res_data["data"], dict):
                    url = res_data["data"].get("url")
                    if url: cdn_urls.append(url)

            if not cdn_urls:
                self._json(422, {
                    "success": False,
                    "message": "Cloudflare cleared, but no active imagery URL found in json tree.",
                    "payload_sent": gen_payload,
                    "response_received": res_data
                })
                return

            # Step 3: Stream and Cache the Generated Images locally
            images = []
            for idx, img_url in enumerate(cdn_urls):
                try:
                    filename = f"zade_forever_{int(time.time())}_{idx}.jpg"
                    local_path = os.path.join(TMP_DIR, filename)
                    
                    # Downloading image assets using the verified Cloudflare context session
                    img_data = scraper.get(img_url, timeout=20)
                    if img_data.status_code == 200:
                        with open(local_path, "wb") as f:
                            f.write(img_data.content)
                        
                        images.append({
                            "url": f"{base_url}?file={filename}",
                            "raw_cdn": img_url
                        })
                except Exception as dl_err:
                    images.append({"error": str(dl_err), "failed_url": img_url})

            self._json(200, {
                "success": True,
                "owner": "@zade4everbot",
                "execution_seconds": round(time.time() - start_time, 2),
                "enhanced": target_prompt != prompt,
                "data": images
            })

        except Exception as global_err:
            self._json(500, {
                "success": False,
                "error": str(global_err),
                "trace": traceback.format_exc()
            })
