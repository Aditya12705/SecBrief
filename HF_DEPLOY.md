# Deploy SecBrief on Hugging Face (all-in-one)

One Space = **Next.js UI + FastAPI API** on a single free URL.

---

## Before you start

1. Push the repo to GitHub (e.g. `secbrief`).
2. Have ready:
   - `ARMORIQ_API_KEY` from [platform.armoriq.ai](https://platform.armoriq.ai)
   - `MISTRAL_API_KEY` from [console.mistral.ai](https://console.mistral.ai)
3. Optional: `GITHUB_TOKEN` for higher GitHub API limits on repo scan.

---

## Step 1 — Create the Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. **Space name:** `secbrief` (or your choice).
3. **License:** MIT (or your preference).
4. **Space SDK:** **Docker** (not Gradio).
5. Create the Space.

---

## Step 2 — Connect your GitHub repo

**Option A — Duplicate HF template (fastest)**

1. On the new Space, open **Files** → **Add file** → upload/connect repo.
2. Or: **Settings → Repository** → link `your-username/secbrief` on GitHub.

**Option B — Push from local**

```powershell
cd d:\Luma
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/secbrief
git push hf main
```

Replace `YOUR_USERNAME` and `secbrief` with your HF user and Space name.

---

## Step 3 — Space README (required metadata)

HF needs Docker metadata in the Space **`README.md`** at the repo root.

Either:

- **Rename** `README_HF.md` → `README.md` on a deploy branch, **or**
- Copy the YAML block from `README_HF.md` to the **top** of the Space README on the HF website.

The top of `README.md` must look like:

```yaml
---
title: SecBrief
emoji: 🛡️
colorFrom: amber
colorTo: green
sdk: docker
app_port: 7860
---
```

---

## Step 4 — Dockerfile location

The repo root must contain:

- `Dockerfile` (already in this project)
- `backend/`
- `frontend/`

HF builds automatically when you push. First build takes **5–10 minutes**.

---

## Step 5 — Secrets (Settings → Variables)

In the Space → **Settings** → **Repository secrets** (or Variables):

| Variable | Required | Notes |
|----------|----------|--------|
| `ARMORIQ_API_KEY` | Yes | `ak_live_...` or test key |
| `MISTRAL_API_KEY` | Yes | Mistral API key |
| `MISTRAL_MODEL` | No | Default `mistral-small-latest` |
| `GITHUB_TOKEN` | No | `ghp_...` for repo scans |

Do **not** commit `.env` to GitHub.

---

## Step 6 — Wait for build

1. Open the Space **Logs** tab.
2. Wait until you see Uvicorn running on port **7860**.
3. Open the public URL:  
   `https://huggingface.co/spaces/YOUR_USERNAME/secbrief`

If build fails, check Logs for `npm run build` or `pip install` errors.

---

## Step 7 — Smoke test

1. Open your Space URL in the browser.
2. **Code** tab → Load SQLi sample → **Audit code**.
3. Enable **Attack-the-agent** → **Generate verified fix plan**.
4. Confirm **BLOCK** on `delete_all` and an intent receipt.

API health: `https://huggingface.co/spaces/YOUR_USERNAME/secbrief/health`  
(API docs: add `/docs` to the same host.)

---

## Before a live demo

HF free Spaces **sleep when idle**. 1–2 minutes before presenting:

1. Open the Space URL.
2. Hit `/health` once.
3. Run through one quick code audit so the Space is warm.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails on `npm run build` | Run `cd frontend && npm run build` locally; fix errors, push again |
| White page | Check Logs; confirm `static/` was copied (Docker build stage) |
| API errors | Verify secrets in Space Settings |
| GitHub scan rate limit | Add `GITHUB_TOKEN` secret |
| Slow first request | Normal after sleep — warm up before demo |

---

## Local test (same as HF)

```powershell
cd d:\Luma
docker build -t secbrief .
docker run -p 7860:7860 --env-file .env secbrief
```

Open http://localhost:7860

---

## What you submit to judges

**One link:** `https://huggingface.co/spaces/YOUR_USERNAME/secbrief`

No Vercel, no Railway, no CORS split.
