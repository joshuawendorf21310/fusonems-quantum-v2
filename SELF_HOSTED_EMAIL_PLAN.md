# Self-Hosted Email Integration Plan

**Status:** Email is now **SMTP/IMAP (Mailu) by default**. All outbound (comms, founder dashboard, founder billing statements) and inbound (IMAP poll) use your own server. Postmark is optional; if not configured, Postmark webhooks return 501 and you use `POST /api/email/poll-inbound` for inbound.

**Founder vs aliases:** Set `FOUNDER_EMAIL` (e.g. joshua.j.wendorf@fusionemsquantum.com) for the founder identity; dashboard sends and reply-to use this. Set `BILLING_FROM_EMAIL` (e.g. billing@fusionemsquantum.com) for patient statements, and `SUPPORT_EMAIL` for contact/support; both can point to the same alias or different ones. `NOREPLY_EMAIL` is used for system notifications when set.

## 0. Mailu Mail Server Setup (Recommended)

### Deploy Mailu (Docker, easy setup)
1. Create a new VPS (DigitalOcean droplet or similar, Ubuntu recommended).
2. Point your domain/subdomain (e.g., mail.yourdomain.com) to your server’s IP in DigitalOcean DNS.
3. Clone Mailu setup:
	```bash
	git clone https://github.com/Mailu/Mailu.git
	cd Mailu
	cp .env.sample .env
	# Edit .env for your domain, admin, etc.
	docker compose up -d
	```
4. Access the Mailu admin panel at https://mail.yourdomain.com/admin
5. Add users, aliases, domains, and adjust all settings as needed.

### DigitalOcean DNS Records
- **MX**: Points to mail.yourdomain.com
- **A**: mail.yourdomain.com → your server IP
- **SPF**: `v=spf1 mx ~all`
- **DKIM**: Generated in Mailu admin, add as TXT
- **DMARC**: `v=DMARC1; p=none; rua=mailto:postmaster@yourdomain.com`

Wait for DNS to propagate. Test with https://mxtoolbox.com/


## 1. Mail Server Setup (Summary)
- Mailu, Mailcow, or Poste.io all work; Mailu is recommended for simplicity and full control.
- Requirements: VPS, domain, open ports (25, 587, 993, 995).


## 2. Backend Integration
- Outbound: Use SMTP (Python's smtplib or aiosmtplib) to send mail via your Mailu server.
- Inbound: Use IMAP (Python's imaplib or aioimaplib) to fetch mail from your Mailu server.
- Update `/backend/services/email/email_transport_service.py` to use SMTP (configurable via environment variables).
- Update `/backend/services/email/email_ingest_service.py` to use IMAP for polling new mail (configurable via environment variables).
- Remove Postmark-specific logic.


## 3. Security
- Use SSL/TLS for all connections (Mailu supports this by default).
- Store credentials securely (use environment variables, never hardcode).


## 4. Frontend
- No changes needed for backend switch; API remains the same.
- UI can be upgraded for Gmail-like experience (inbox, compose, folders, search, etc.).


## 5. Maintenance
- Monitor server for spam/blacklisting (Mailu admin panel, mxtoolbox.com, etc.).
- Regularly update mail server software (docker compose pull && docker compose up -d).

---

**Next Steps:**
1. Deploy Mailu (or your preferred mail server) and configure DNS on DigitalOcean.
2. Update backend to use SMTP/IMAP (Mailu credentials).
3. Test sending/receiving from your platform.
4. Upgrade frontend UI for Gmail-like experience.
