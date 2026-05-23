import sys
import json
import time
import os
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler
from datetime import datetime

# pip install microsoftdesigner
try:
    from microsoftdesigner.gen_images import create_img
except ImportError:
    create_img = None

# ── Credentials ───────────────────────────────────────────────
# Get from designer.microsoft.com → DevTools/Eruda → Network → DallE.ashx request
USER_ID    = "8a4225c395d20d84"
AUTH_TOKEN = "Bearer eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkExMjhDQkMtSFMyNTYiLCJ4NXQiOiJLN213NFpBaEZPOGowaHdEa0Z3VTBqMi1ndEUiLCJ6aXAiOiJERUYifQ.U3UeHPRR1uomS2YXuZQqpttq3Nsjb6hVIo1c6NW4L7WhHtR0BSp8b7fcBxyPyg_oxrgbzdt-4N1ny6eL-pJ4waTsKMJymWSManS4ZZq3vE4sUoUZ7Q92H66_lBQidUqrlZNmFBjaMGU5zTuUYrnJkldwmuzBD5FH_CRpdzXb5gc3eJ1qjDrtj2ABVZRD_CFVTthBJuu1lD8L7wvOodrGq9a7ryV-3TaGAHkTul6uz4hAPOwol1msvESR1QtZpfqirF9DKJaLbsRF1BlBVBCRuk_Q5YjdaTlKUO25T1qj53_nw6_YLXZu3mSUSyHZjQtSrJpg6D_7btm7XBVFAfWw_A.9jjzAlx-2wkebA9_krU2xg.hMVFVSL__8s09UAQqfIvBRN5S3j-0EvB7yt6kOaoJmyZzhPedi14-50TlqbotEQBH1gVYRatFtBHumpOvnrZr-QzKwk_iNd8FF8KQe7Eh9EH-ddVzQtT4KN3rthkUBvyVx_unmCOZrNFpGwm3dmuN6Uv9YeG1X8XnQXOYzwgGaY6UnNwErOoIRiV3dlhi7_Xqk4QI7HKJ6io_S9he7Q6W1uJFsAaRNvjPr22t80vTmB-5ioTgnk0ixVqnSp07EoEhnbTKgrOPSfG2PBSbhqOWs4o0xY1I6KVKqltxZN-LnjeNWUSCHE5ZwXfQOyrSMFwzk0xLi7Goq3H1ysng9Za4AbEhrBqUklxh_x7uxo_fHby2VadB0mdu1czl1ew9r072AiYi8plHfxomhc-aMq8Entn50iwmp7eLNteaIj5SJOT2hCe-7XxNcFsQvxejC5Ebjn43ZDCuIX3V8W2cNsZmL3RWg1BUrEOOG0Ov5-njrUhYutf6qepm9ImlY5vDWF4pVW5ikb2NrqHEpKjH6EgpFKNtl1BPVhRRvq1DJ3QajfucS_6WloRl8NPUMxbcj2LdOisF9Xny6M1p48c3ym3hbuHjNV9noNTRiIJP7h-IC4TMugWFOWLCCLJZ0VHRF5Bs_JCmHk4DzoOON4yeIB8TfO_kKGhSxYSh4tDaLsPiycUYyudnBAOGmVGIEZgI2yHzzH6EEB2nS9vBAjUcWKyyeVxqM6xRyX5ltAOZpqIIRLcmTd3e8WKmunOhjVNyUF9UOqKuohAdSwHy2HRLq9j8L3nDmhWXdFmkVcMd9art2m_WHC37lM3GRtH0CgezKt-8JQE6rTYb6U4rv0x5gWA6t6-zxN_dV9cUTm4dKeCyu4UR3QsG8ymIS04SB909FGIWMogS-ydqvJjUiF4NzvWvp2HwCCsh2NRMRR98EogTkZO3fWK7r3oAL-jUcheM5ImOmR-KRqU-IRepb7eP7x_0uT2zRC1UDKwb-rs85yHk8D2kaDEDxT2Hes8OrflRzLl6PpuS0MiW5mDJH14mH2x7jzzvCBRF-5QWfwSyqBbUSTj2NhXqyhySQK9kc_nbcGYuVlFeMyAm4VbPuHATMme1Jzdw_TkJvMerqfjWFvUHp2hkqs710W9j-KoICjE96ivbXRwYxQnQxegF6Is5hLDEnfNT4H6rVPM4BFHt0MYsiw-SbAA1taiivEr5iAQyut0fIYYTP-X_6gEbPK3xkzrUh6HZuyaNQ0MCcv94haHcnkTkNY5OaIeFmjDgn4dsDqi_mnYmaBx3EHWI2nsPbFg_ion9nrmNFl6EBkFtlrcX2RwYj1PgARYTq2vkPRPJT15TmYC6xUxJb9uwxtQmHeHB8NuzHo6X6VnftTe2Yr-CZhjHQNaZU4ObinBvB1ZY0KOutXQcJLuiFXNnsVy8mdYvBrmVWBv0bi0e-U8oBgvOY02Kicvyyr41D-9VEmykw4HL8UO5d8lRqMIrO_9DMHMxD6cb-MfVx6KJ1xk5gVnIC8VFK2Yaz44DD0Omf2li9w8.4h3IqkM1xPMoI62y7w9kAA"

# Resolution mapping
RESOLUTION_MAP = {
    "square":    "1024x1024",
    "portrait":  "1024x1792",
    "landscape": "1792x1024",
}


class handler(BaseHTTPRequestHandler):

    def _json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Powered-By", "Zade-Designer-API")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=4).encode("utf-8"))

    def do_OPTIONS(self):
        self._json(200, {})

    def do_GET(self):
        if create_img is None:
            self._json(500, {
                "success": False,
                "code": "MISSING_DEPENDENCY",
                "message": "microsoftdesigner package not installed. Add it to requirements.txt",
            })
            return

        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

        prompt     = qs.get("prompt",     [""])[0].strip()
        aspect     = qs.get("aspect",     ["square"])[0].strip().lower()
        boost      = int(qs.get("boost",  ["1"])[0])
        seed_raw   = qs.get("seed",       [None])[0]
        seed       = int(seed_raw) if seed_raw else None

        # Override creds via headers (optional)
        user_id    = self.headers.get("X-User-Id",    USER_ID)
        auth_token = self.headers.get("X-Auth-Token", AUTH_TOKEN)

        print(f"[DESIGNER] [{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] prompt='{prompt}' aspect={aspect}")

        if not prompt:
            self._json(400, {
                "success": False,
                "owner": "@zade4everbot",
                "code": "MISSING_PROMPT",
                "message": "prompt parameter is required.",
            })
            return

        if not user_id or user_id == "REPLACE_YOUR_USER_ID_HERE":
            self._json(503, {
                "success": False,
                "owner": "@zade4everbot",
                "code": "NO_CREDENTIALS",
                "message": "USER_ID / AUTH_TOKEN not configured in designer.py",
            })
            return

        resolution = RESOLUTION_MAP.get(aspect, "1024x1024")

        start = time.time()
        try:
            # Fix 1: Ensure local temp folder exists for Vercel Serverless environment
            os.makedirs("/tmp/designer_imgs", exist_ok=True)

            # Fix 2: Run sync execution directly. Vercel's wrapper handles runtime execution.
            image_paths = create_img(
                user_id=user_id,
                auth_token=auth_token,
                prompt=prompt,
                save_path="/tmp/designer_imgs",
                resolution=resolution,
                boost_count=boost,
                seed=seed,
            )

            elapsed = round(time.time() - start, 2)

            if not image_paths:
                self._json(403, {
                    "success": False,
                    "owner": "@zade4everbot",
                    "code": "NO_CREDITS_OR_REJECTED",
                    "message": "Designer returned no images — credits exhausted or prompt blocked.",
                    "elapsed_seconds": elapsed,
                })
                return

            # Convert local paths → base64 format response
            import base64

            images = []
            for path in image_paths:
                try:
                    with open(path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    images.append({
                        "base64": b64,
                        "format": "jpeg",
                        "local_path": path,
                    })
                    # Fix 3: Instantly delete file from disk after encoding to free serverless RAM
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    images.append({"error": str(e), "local_path": path})

            self._json(200, {
                "success": True,
                "owner": "@zade4everbot",
                "source": "Microsoft Designer (GPT-4o)",
                "elapsed_seconds": elapsed,
                "configuration": {
                    "resolution": resolution,
                    "aspect": aspect,
                    "boost": boost,
                    "seed": seed,
                },
                "total_images": len(images),
                "images": images,
            })

            print(f"[DESIGNER] Done in {elapsed}s — {len(images)} images")

        except Exception as e:
            elapsed = round(time.time() - start, 2)
            
            # Fix 4: Capture detailed stack trace if it still encounters internal errors
            err_details = traceback.format_exc()
            err = str(e)
            print(f"[DESIGNER ERROR]\n{err_details}")

            if "403" in err or "credit" in err.lower():
                code = "CREDITS_EXHAUSTED"
                msg  = "Auth token expired or credits exhausted. Refresh your AUTH_TOKEN."
            elif "401" in err or "auth" in err.lower() or "token" in err.lower():
                code = "AUTH_FAILED"
                msg  = "Invalid USER_ID or AUTH_TOKEN. Get fresh values from DevTools."
            else:
                code = "INTERNAL_FAULT"
                msg  = "Unexpected error during generation."

            self._json(500, {
                "success": False,
                "owner": "@zade4everbot",
                "code": code,
                "message": msg,
                "details": err_details,
                "elapsed_seconds": elapsed,
                "context": {"runtime": f"Python {sys.version.split()[0]}"},
            })
