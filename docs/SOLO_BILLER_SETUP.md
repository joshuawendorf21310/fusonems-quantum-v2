# Solo Biller + AI Setup (You're the Only Biller)

**You are the only biller.** This guide gets you to **AI handling phone calls** and **AI assisting you with billing** (explanations, what to do next, chat) so you can focus on following the AI’s guidance. The platform is built for a single biller—no queues, no round-robin, AI does as much as possible.

**Where to start (solo biller, new to billing):**
1. Set `OLLAMA_ENABLED=true` and `OLLAMA_SERVER_URL` in `backend/.env`, then install and run [Ollama](https://ollama.com) and pull the model (e.g. `ollama pull llama3.2`).
2. On every **Billing** page in the app you'll see the **Billing AI Assistant** at the bottom — use **Explain a term** and **Ask the AI** for plain-language help and "what to do next."
3. For **phone**: set `APP_BASE_URL` and Telnyx TeXML URL so callers get the IVR; options 1 and 2 are answered by the AI; option 3 transfers to you (optional: `TELNYX_TRANSFER_NUMBER`).

## 1. Phone: AI Answers First (IVR + AI Biller Helper)

When someone calls your Telnyx number, they hear:

- *"Thanks for calling. Press 1 for billing questions. Press 2 for payment status. Press 3 to speak with a representative."*
- **1 or 2:** Ollama answers in plain, human-like language (AI biller helper).
- **3:** Call is transferred to you (or your queue).

**Backend env (e.g. `backend/.env`):**

```bash
# Telnyx (your number +1 (715) 254-3027)
TELNYX_API_KEY=your_key
TELNYX_FROM_NUMBER=+17152543027
TELNYX_ENABLED=true
TELNYX_PUBLIC_KEY=your_public_key
TELNYX_REQUIRE_SIGNATURE=false

# So Telnyx can fetch the menu and choices from your server (use your real API host)
APP_BASE_URL=https://api.fusionemsquantum.com

# Ollama: AI answers options 1 and 2
OLLAMA_ENABLED=true
OLLAMA_SERVER_URL=http://localhost:11434
OLLAMA_IVR_MODEL=llama3.2
```

**Telnyx portal:**

- For your number, set the **TeXML / Call Control URL** (instruction URL) to:
  - `https://api.fusionemsquantum.com/api/telnyx/texml/welcome`
- Use the same host as `APP_BASE_URL` (e.g. `api.fusionemsquantum.com`).

**Optional:** To send “Press 3” callers to a specific line (e.g. your desk):

```bash
TELNYX_TRANSFER_NUMBER=+1XXXXXXXXXX
```

## 2. Billing: AI Explains Everything (Solo Biller, New to Billing)

In the app:

- **Billing pages** show a **Billing AI Assistant** at the bottom with:
  - **Explain a term** – e.g. “denial”, “EOB”, “claim status”, “what to do next”. AI explains in plain language.
  - **Ask the AI** – Free-form questions. AI gives plain-language answers and “what to do next” steps.

The AI is instructed to:

- Do as much of the thinking and next-step planning as possible.
- Explain everything in plain language and define jargon.
- Give clear “what to do next” when relevant.

**Backend env (same as above):**

```bash
OLLAMA_ENABLED=true
OLLAMA_SERVER_URL=http://localhost:11434
```

**Ollama on your machine:**

1. Install [Ollama](https://ollama.com).
2. Run: `ollama pull llama3.2` (or the model you use for `OLLAMA_IVR_MODEL`).
3. Keep Ollama running so the backend can reach `OLLAMA_SERVER_URL`.

## 3. Fax

- **Inbound:** Telnyx sends fax events to your backend; faxes are stored, matched to patients, and you get notified. Configure your Telnyx number’s fax webhook to point at your backend (e.g. `/api/telnyx/fax-received` if you expose it).
- **Outbound:** Use the comms API (e.g. send fax from the app). Set `TELNYX_FAX_FROM_NUMBER` and your fax connection in Telnyx/config.

## 4. Hosting on DigitalOcean

Your app and hosting are both on DigitalOcean (domain: **fusionemsquantum.com**). Use the public URL of your backend so Telnyx and the rest of the internet can reach it.

- **APP_BASE_URL** — Where your backend API is reachable:
  - **Recommended:** `https://api.fusionemsquantum.com` (no trailing slash). Add an A record in **DigitalOcean Networking → Domains** pointing `api.fusionemsquantum.com` to your droplet (or App Platform endpoint).
  - Without a subdomain: use your droplet IP with HTTPS if you have SSL, e.g. `https://YOUR_DROPLET_IP`.
- **Telnyx TeXML URL** — In the Telnyx portal, set your number’s instruction URL to:
  - `https://api.fusionemsquantum.com/api/telnyx/texml/welcome`
- **OLLAMA_SERVER_URL** — If Ollama runs on the **same droplet** as the backend, use `http://localhost:11434`. If it runs elsewhere, use that machine’s URL.

**On the droplet:** Bind the backend to `0.0.0.0` and allow inbound traffic on your API port (e.g. 8000) in the **DigitalOcean firewall** (or use a reverse proxy like Nginx with SSL). If you use **DigitalOcean App Platform**, set `APP_BASE_URL` and the TeXML URL to the URL App Platform gives your API service.

## 5. Quick Checklist

| Goal                         | What to set                                      |
|-----------------------------|---------------------------------------------------|
| AI answers billing calls   | `APP_BASE_URL`, `OLLAMA_*`, Telnyx TeXML URL     |
| AI explains billing in app | `OLLAMA_ENABLED=true`, `OLLAMA_SERVER_URL`       |
| “Press 3” goes to you     | `TELNYX_TRANSFER_NUMBER` (optional)               |
| Fax in/out                 | Telnyx fax webhook, `TELNYX_FAX_FROM_NUMBER`     |

You’re the only biller and new to billing: use **Explain a term** and **Ask the AI** on every billing page; the AI is set up to do as much as possible and explain everything in plain language.
