import sys
import json
import time
import os
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler
from datetime import datetime

try:
    from microsoftdesigner.gen_images import create_img
except ImportError:
    create_img = None

# ── Copilot / Designer Fresh Credentials ──────────────────────
USER_ID    = "8a4225c395d20d84"
AUTH_TOKEN = "Bearer eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkExMjhDQkMtSFMyNTYiLCJ4NXQiOiJLN213NFpBaEZPOGowaHdEa0Z3VTBqMi1ndEUiLCJ6aXAiOiJERUYifQ.U3UeHPRR1uomS2YXuZQqpttq3Nsjb6hVIo1c6NW4L7WhHtR0BSp8b7fcBxyPyg_oxrgbzdt-4N1ny6eL-pJ4waTsKMJymWSManS4ZZq3vE4sUoUZ7Q92H66_lBQidUqrlZNmFBjaMGU5zTuUYrnJkldwmuzBD5FH_CRpdzXb5gc3eJ1qjDrtj2ABVZRD_CFVTthBJuu1lD8L7wvOodrGq9a7ryV-3TaGAHkTul6uz4hAPOwol1msvESR1QtZpfqirF9DKJaLbsRF1BlBVBCRuk_Q5YjdaTlKUO25T1qj53_nw6_YLXZu3mSUSyHZjQtSrJpg6D_7btm7XBVFAfWw_A.9jjzAlx-2wkebA9_krU2xg.hMVFVSL__8s09UAQqfIvBRN5S3j-0EvB7yt6kOaoJmyZzhPedi14-50TlqbotEQBH1gVYRatFtBHumpOvnrZr-QzKwk_iNd8FF8KQe7Eh9EH-ddVzQtT4KN3rthkUBvyVx_unmCOZrNFpGwm3dmuN6Uv9YeG1X8XnQXOYzwgGaY6UnNwErOoIRiV3dlhi7_Xqk4QI7HKJ6io_S9he7Q6W1uJFsAaRNvjPr22t80vTmB-5ioTgnk0ixVqnSp07EoEhnbTKgrOPSfG2PBSbhqOWs4o0xY1I6KVKqltxZN-LnjeNWUSCHE5ZwXfQOyrSMFwzk0xLi7Goq3H1ysng9Za4AbEhrBqUklxh_x7uxo_fHby2VadB0mdu1czl1ew9r072AiYi8plHfxomhc-aMq8Entn50iwmp7eLNteaIj5SJOT2hCe-7XxNcFsQvxejC5Ebjn43ZDCuIX3V8W2cNsZmL3RWg1BUrEOOG0Ov5-njrUhYutf6qepm9ImlY5vDWF4pVW5ikb2NrqHEpKjH6EgpFKNtl1BPVhRRvq1DJ3QajfucS_6WloRl8NPUMxbcj2LdOisF9Xny6M1p48c3ym3hbuHjNV9noNTRiIJP7h-IC4TMugWFOWLCCLJZ0VHRF5Bs_JCmHk4DzoOON4yeIB8TfO_kKGhSxYSh4tDaLsPiycUYyudnBAOGmVGIEZgI2yHzzH6EEB2nS9vBAjUcWKyyeVxqM6xRyX5ltAOZpqIIRLcmTd3e8WKmunOhjVNyUF9UOqKuohAdSwHy2HRLq9j8L3nDmhWXdFmkVcMd9art2m_WHC37lM3GRtH0CgezKt-8JQE6rTYb6U4rv0x5gWA6t6-zxN_dV9cUTm4dKeCyu4UR3QsG8ymIS04SB909FGIWMogS-ydqvJjUiF4NzvWvp2HwCCsh2NRMRR98EogTkZO3fWK7r3oAL-jUcheM5ImOmR-KRqU-IRepb7eP7x_0uT2zRC1UDKwb-rs85yHk8D2kaDEDxT2Hes8OrflRzLl6PpuS0MiW5mDJH14mH2x7jzzvCBRF-5QWfwSyqBbUSTj2NhXqyhySQK9kc_nbcGYuVlFeMyAm4VbPuHATMme1Jzdw_TkJvMerqfjWFvUHp2hkqs710W9j-KoICjE96ivbXRwYxQnQxegF6Is5hLDEnfNT4H6rVPM4BFHt0MYsiw-SbAA1taiivEr5iAQyut0fIYYTP-X_6gEbPK3xkzrUh6HZuyaNQ0MCcv94haHcnkTkNY5OaIeFmjDgn4dsDqi_mnYmaBx3EHWI2nsPbFg_ion9nrmNFl6EBkFtlrcX2RwYj1PgARYTq2vkPRPJT15TmYC6xUxJb9uwxtQmHeHB8NuzHo6X6VnftTe2Yr-CZhjHQNaZU4ObinBvB1ZY0KOutXQcJLuiFXNnsVy8mdYvBrmVWBv0bi0e-U8oBgvOY02Kicvyyr41D-9VEmykw4HL8UO5d8lRqMIrO_9DMHMxD6cb-MfVx6KJ1xk5gVnIC8VFK2Yaz44DD0Omf2li9w8.4h3IqkM1xPMoI62y7w9kAA"

TMP_DIR = "/tmp/designer_imgs"

class handler(BaseHTTPRequestHandler):

    def _json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Powered-By", "Zade-Copilot-Core")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=4).encode("utf-8"))

    def do_OPTIONS(self):
        self._json(200, {})

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed_url.query)

        # ── Route: Serve Image File ─────────────────────────────
        if "file" in qs:
            filename = os.path.basename(qs["file"][0].strip())
            file_path = os.path.join(TMP_DIR, filename)
            
            if os.path.exists(file_path):
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    with open(file_path, "rb") as f:
                        self.wfile.write(f.read())
                    return
                except Exception as e:
                    self._json(500, {"success": False, "message": str(e)})
                    return
            else:
                self._json(404, {"success": False, "message": "Image expired or file not found."})
                return

        # ── Route: Image Generation ─────────────────────────────
        if create_img is None:
            self._json(500, {"success": False, "message": "Library missing."})
            return

        prompt = qs.get("prompt", [""])[0].strip()
        if not prompt:
            self._json(400, {"success": False, "message": "prompt is required."})
            return

        host = self.headers.get("Host", "zade-copimg-api.vercel.app")
        base_url = f"https://{host}{parsed_url.path}"

        start = time.time()
        try:
            os.makedirs(TMP_DIR, exist_ok=True)

            # CRITICAL JUGAD: Pass boost_count=0 to run on Copilot's unlimited/slow standard engine 
            image_paths = create_img(
                user_id=USER_ID,
                auth_token=AUTH_TOKEN,
                prompt=prompt,
                save_path=TMP_DIR,
                resolution="1024x1024",
                boost_count=0, # 0 = Unlimited Free Queue, no credits deducted!
                seed=None,
            )

            elapsed = round(time.time() - start, 2)

            if not image_paths:
                self._json(403, {"success": False, "message": "Generation failed or token dead."})
                return

            images = []
            for path in image_paths:
                filename = os.path.basename(path)
                images.append({
                    "url": f"{base_url}?file={filename}",
                    "filename": filename
                })

            self._json(200, {
                "success": True,
                "owner": "@zade4everbot",
                "elapsed_seconds": elapsed,
                "total_images": len(images),
                "images": images
            })

        except Exception as e:
            self._json(500, {
                "success": False,
                "code": "INTERNAL_FAULT",
                "message": str(e),
                "details": traceback.format_exc()
            })
