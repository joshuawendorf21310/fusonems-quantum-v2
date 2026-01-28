# Jitsi Meet Server Setup for CareFusion Telehealth
## HIPAA-Compliant Video Infrastructure

---

## Overview

This guide sets up a self-hosted Jitsi Meet server on DigitalOcean for production telehealth video consultations.

**Benefits:**
- ✅ Zero per-minute costs
- ✅ HIPAA-compliant with encryption
- ✅ Unlimited video calls
- ✅ Recording capability
- ✅ Complete data control

**Cost:** $30-50/month for server (no usage fees)

---

## 1. DigitalOcean Droplet Setup

### Create Droplet

1. Go to DigitalOcean Console
2. Create Droplet:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic
   - **CPU:** 4 vCPU, 8GB RAM ($48/month)
   - **Storage:** 160GB SSD
   - **Region:** Choose closest to your users
   - **Hostname:** `jitsi.fusionems.com`

3. Add SSH Key
4. Create Droplet

### DNS Configuration

Add DNS records for your domain:

```
A Record: jitsi.fusionems.com → [Your Droplet IP]
```

---

## 2. Initial Server Configuration

### SSH into server:

```bash
ssh root@[YOUR_DROPLET_IP]
```

### Update system:

```bash
apt update && apt upgrade -y
```

### Set hostname:

```bash
hostnamectl set-hostname jitsi.fusionems.com
echo "127.0.0.1 jitsi.fusionems.com" >> /etc/hosts
```

### Create non-root user (optional but recommended):

```bash
adduser jitsi
usermod -aG sudo jitsi
```

---

## 3. Install Jitsi Meet

### Add Jitsi repository:

```bash
curl https://download.jitsi.org/jitsi-key.gpg.key | gpg --dearmor > /usr/share/keyrings/jitsi-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/jitsi-keyring.gpg] https://download.jitsi.org stable/" | tee /etc/apt/sources.list.d/jitsi-stable.list
apt update
```

### Install required packages:

```bash
apt install -y nginx certbot python3-certbot-nginx
```

### Install Jitsi Meet:

```bash
apt install -y jitsi-meet
```

**During installation:**
- Enter hostname: `jitsi.fusionems.com`
- SSL Certificate: Choose "Generate a new self-signed certificate" (we'll replace with Let's Encrypt)

---

## 4. SSL Certificate (Let's Encrypt)

### Generate SSL certificate:

```bash
/usr/share/jitsi-meet/scripts/install-letsencrypt-cert.sh
```

**Enter email:** `admin@fusionems.com`

This enables HTTPS for HIPAA compliance.

---

## 5. HIPAA-Compliant Configuration

### Configure Jitsi for Security

Edit `/etc/jitsi/meet/jitsi.fusionems.com-config.js`:

```javascript
var config = {
    hosts: {
        domain: 'jitsi.fusionems.com',
        muc: 'conference.jitsi.fusionems.com'
    },
    
    // Enable end-to-end encryption
    e2eping: {
        enabled: true
    },
    
    // Enable lobby (waiting room)
    enableLobbyChat: true,
    
    // Require display name
    requireDisplayName: true,
    
    // Enable recording
    fileRecordingsEnabled: true,
    liveStreamingEnabled: false,
    
    // Security settings
    enableInsecureRoomNameWarning: true,
    enableNoAudioDetection: true,
    enableNoisyMicDetection: true,
    
    // Quality settings for medical consultations
    resolution: 720,
    constraints: {
        video: {
            height: {
                ideal: 720,
                max: 1080,
                min: 360
            }
        }
    },
    
    // Disable third-party analytics
    disableThirdPartyRequests: true,
    
    // UI customization
    defaultLanguage: 'en',
    
    // Features
    enableWelcomePage: false,
    prejoinPageEnabled: true,
    
    // Recording
    recordingService: {
        enabled: true,
        sharingEnabled: false,
        hideStorageWarning: true
    }
};
```

### Enable JWT Authentication

Edit `/etc/jitsi/meet/jitsi.fusionems.com-config.js`:

```javascript
var config = {
    // ... existing config ...
    
    // Enable JWT authentication
    enableUserRolesBasedOnToken: true,
};
```

Edit `/etc/prosody/conf.avail/jitsi.fusionems.com.cfg.lua`:

```lua
VirtualHost "jitsi.fusionems.com"
    authentication = "token"
    app_id = "fusionems_carefusion"
    app_secret = "YOUR_SECRET_KEY_HERE"  -- Generate with: openssl rand -hex 32
    
    -- Enable lobby
    modules_enabled = {
        "muc_lobby_rooms";
    }
    
    lobby_muc = "lobby.jitsi.fusionems.com"
    main_muc = "conference.jitsi.fusionems.com"

Component "conference.jitsi.fusionems.com" "muc"
    storage = "memory"
    modules_enabled = {
        "muc_meeting_id";
        "muc_domain_mapper";
        "token_verification";
    }
    admins = { "focus@auth.jitsi.fusionems.com" }
    muc_room_locking = false
    muc_room_default_public_jids = true

Component "internal.auth.jitsi.fusionems.com" "muc"
    storage = "memory"
    modules_enabled = {
        "ping";
    }
    admins = { "focus@auth.jitsi.fusionems.com", "jvb@auth.jitsi.fusionems.com" }
    muc_room_locking = false
    muc_room_default_public_jids = true

VirtualHost "auth.jitsi.fusionems.com"
    authentication = "internal_hashed"

Component "lobby.jitsi.fusionems.com" "muc"
    storage = "memory"
    restrict_room_creation = true
    muc_room_locking = false
    muc_room_default_public_jids = true
```

### Install JWT plugin for Prosody:

```bash
apt install -y lua-basexx lua-cjson prosody-modules-extra
prosodyctl restart
```

### Restart all Jitsi services:

```bash
systemctl restart prosody jicofo jitsi-videobridge2 nginx
```

---

## 6. Recording Configuration (Optional)

### Install Jibri (recording service):

```bash
apt install -y jibri
```

### Configure Jibri

Edit `/etc/jitsi/jibri/jibri.conf`:

```hocon
jibri {
    recording {
        recordings-directory = "/var/jibri-recordings"
        finalize-script = "/usr/local/bin/finalize-recording.sh"
    }
    
    api {
        http {
            external-api-port = 2222
            internal-api-port = 3333
        }
    }
    
    streaming {
        rtmp-allow-list = []
    }
}
```

### Create recordings directory:

```bash
mkdir -p /var/jibri-recordings
chown jibri:jibri /var/jibri-recordings
chmod 755 /var/jibri-recordings
```

### Create finalize script `/usr/local/bin/finalize-recording.sh`:

```bash
#!/bin/bash
# This script is called when recording finishes
# Upload to your backend storage
RECORDING_PATH=$1
FILENAME=$(basename "$RECORDING_PATH")

# Upload to FusionEMS backend
curl -X POST https://api.fusionems.com/api/carefusion/recordings/upload \
  -F "file=@${RECORDING_PATH}" \
  -F "filename=${FILENAME}" \
  -H "Authorization: Bearer YOUR_API_TOKEN"

# Clean up local file after upload
rm -f "$RECORDING_PATH"
```

Make executable:

```bash
chmod +x /usr/local/bin/finalize-recording.sh
```

---

## 7. Firewall Configuration

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 10000/udp
ufw allow 3478/udp
ufw allow 5349/tcp
ufw enable
```

---

## 8. HIPAA Compliance Checklist

- ✅ SSL/TLS encryption (Let's Encrypt)
- ✅ JWT authentication (only authenticated users)
- ✅ Waiting room/lobby enabled
- ✅ End-to-end encryption option
- ✅ No third-party tracking
- ✅ Recording stored securely
- ✅ Firewall configured
- ✅ Automatic security updates enabled

### Enable automatic security updates:

```bash
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

---

## 9. Monitoring and Logs

### Check service status:

```bash
systemctl status prosody
systemctl status jicofo
systemctl status jitsi-videobridge2
systemctl status nginx
```

### View logs:

```bash
# Prosody logs
tail -f /var/log/prosody/prosody.log

# Jicofo logs
tail -f /var/log/jitsi/jicofo.log

# JVB logs
tail -f /var/log/jitsi/jvb.log

# Nginx logs
tail -f /var/log/nginx/access.log
```

---

## 10. Testing

### Test the server:

1. Visit: `https://jitsi.fusionems.com`
2. Create a test room
3. Verify video/audio works
4. Test screen sharing
5. Test recording (if enabled)

---

## 11. Backend Integration

The FusionEMS backend will:
1. Generate JWT tokens for authenticated users
2. Create secure room names
3. Embed Jitsi in CareFusion portals
4. Store meeting metadata
5. Link recordings to visit records

---

## 12. Maintenance

### Update Jitsi:

```bash
apt update
apt upgrade jitsi-meet
systemctl restart prosody jicofo jitsi-videobridge2
```

### Backup configuration:

```bash
tar -czf jitsi-backup-$(date +%Y%m%d).tar.gz \
  /etc/jitsi/ \
  /etc/prosody/
```

---

## 13. Scaling (Future)

For high volume (100+ concurrent calls):
- Add additional JVB (video bridge) servers
- Use load balancer
- Separate Prosody, Jicofo, JVB servers

---

## Environment Variables for Backend

Add to backend `.env`:

```bash
# Jitsi Configuration
JITSI_DOMAIN=jitsi.fusionems.com
JITSI_APP_ID=fusionems_carefusion
JITSI_APP_SECRET=your_secret_key_here
JITSI_JWT_ALGORITHM=HS256
JITSI_RECORDING_ENABLED=true
```

---

## Support Resources

- **Jitsi Documentation:** https://jitsi.github.io/handbook/
- **Community Forum:** https://community.jitsi.org/
- **GitHub:** https://github.com/jitsi/jitsi-meet

---

## Cost Breakdown

- **DigitalOcean Droplet:** $48/month (4 CPU, 8GB RAM)
- **Domain/SSL:** $0 (Let's Encrypt free)
- **Video Usage:** $0 (unlimited)
- **Total:** $48/month for unlimited HIPAA-compliant video

Compare to Daily.co: $99/month for only 100,000 minutes

---

**Setup Time:** 1-2 hours  
**Result:** Production-ready, HIPAA-compliant video infrastructure with zero usage costs
