# Founder Account Setup

This guide explains how to set up the founder account for FusionEMS Quantum.

## Quick Setup

Run the setup script to create or update the founder user account:

```bash
cd /root/fusonems-quantum-v2
python3 scripts/setup_founder_user.py
```

## Credentials

The script sets up the following founder account:

- **Email:** `joshua.j.wendorf@fusionemsquantum.com`
- **Password:** `Addyson21310#`
- **Role:** `founder`
- **Organization:** `Fusion EMS Quantum`

## What the Script Does

1. **Creates or finds the organization** "Fusion EMS Quantum"
2. **Creates or updates the founder user** with:
   - Email: `joshua.j.wendorf@fusionemsquantum.com`
   - Password: `Addyson21310#` (hashed securely)
   - Role: `founder`
   - Full name: `Joshua Wendorf`
3. **Ensures the user has founder permissions** and correct password
4. **Removes any password change requirements** so you can log in immediately

## After Setup

Once the script completes successfully, you can:

1. Navigate to `/login` in your browser
2. Log in with:
   - Email: `joshua.j.wendorf@fusionemsquantum.com`
   - Password: `Addyson21310#`
3. You will be automatically redirected to `/founder` dashboard

## Troubleshooting

### Script fails with import errors

Make sure you're running from the project root and that the backend dependencies are installed:

```bash
cd /root/fusonems-quantum-v2/backend
pip install -r requirements.txt
```

### Database connection errors

Ensure your database is running and the `.env` file has the correct `DATABASE_URL` configured.

### User already exists but can't log in

The script will update the password if the user already exists. If you still can't log in:

1. Run the script again to reset the password
2. Check that the user's role is set to `founder` in the database
3. Verify the email address matches exactly (case-sensitive)

## Security Notes

- The password is stored securely using bcrypt hashing
- Never commit the password to version control
- Change the password after first login if needed via the change password feature
- The dev access button has been removed from the login page for security
