# GitHub Actions Deployment Setup

Automatic deployment to DigitalOcean Droplet on every push to `main`.

**Flow:** `git push` → GitHub Actions → `actions/checkout` → rsync → SSH → `docker compose up -d --build` → running app

The Droplet does **not** clone the repo, does **not** need GitHub access, deploy keys, or PATs. Code is pushed from CI via rsync.

## 1. GitHub Secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

All four secrets are required. If `DEPLOY_HOST` is missing you’ll see: `Could not resolve hostname`.

| Secret | Value |
|--------|-------|
| `DEPLOY_HOST` | Droplet IP (e.g. `157.245.6.217`) |
| `DEPLOY_USER` | `deploy` |
| `DEPLOY_KEY` | Full private SSH key. Paste the **entire** key including `-----BEGIN...` and `-----END...`. No extra spaces or CRLF. |
| `DEPLOY_PATH` | `/var/www/fusionems` |
| `DEPLOY_HOST_FINGERPRINT` | (optional) Host key fingerprint, e.g. `SHA256:xD8Uav7MSfHrCUo7EFVAnYgnQ2CKMD6gEM00aCstr/g` – verifies you connect to the right server |

## 2. Droplet Setup (one-time)

```bash
# Create deploy user
sudo adduser deploy
sudo usermod -aG docker deploy
sudo usermod -aG sudo deploy  # optional, for nginx reload

# Create app directory (code is synced by GitHub Actions—no clone needed)
sudo mkdir -p /var/www/fusionems
sudo chown -R deploy:deploy /var/www/fusionems

# backend/.env: created from .env.example on first deploy if missing; never overwritten by CI (excluded from rsync)

# SSH key for GitHub Actions → Droplet
sudo mkdir -p /home/deploy/.ssh
sudo nano /home/deploy/.ssh/authorized_keys  # paste the *public* key (pair of DEPLOY_KEY)
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys
```

## 3. Verify

Push to `main`:

```bash
git push origin main
```

Check **Actions** in GitHub to see the deploy run. Code is synced via rsync (no git pull on server).

## Troubleshooting

- **`error in libcrypto` / `Permission denied (publickey)`** – `DEPLOY_KEY` format issue. Re-add the secret: copy the full private key (from `-----BEGIN` to `-----END` inclusive), paste into a plain text editor, ensure no extra spaces or Windows line endings, then paste into GitHub. Use the **private** key; the **public** key goes in `authorized_keys` on the Droplet.
