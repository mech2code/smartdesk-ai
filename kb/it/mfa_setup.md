# Multi-Factor Authentication (MFA) Setup Guide

## Overview
MFA is mandatory for all employees. It adds a second verification step beyond your password, protecting your account even if your password is compromised. MFA is required for VPN, email, and all corporate web portals.

## Supported MFA Methods
| Method | Recommended | Notes |
|---|---|---|
| Microsoft Authenticator app | Yes | Push notifications, fastest |
| Google Authenticator app | Yes | TOTP codes, works offline |
| SMS one-time code | No | Backup only, less secure |
| Hardware token (YubiKey) | For admins | Request from IT |

## Setting Up Microsoft Authenticator (Recommended)

### Step 1: Install the App
- **iOS**: App Store → search "Microsoft Authenticator" → Install
- **Android**: Google Play → search "Microsoft Authenticator" → Install

### Step 2: Register in the Portal
1. From a desktop browser, go to `mfa.company.com`.
2. Sign in with your corporate credentials.
3. Click **Add authentication method** → **Authenticator app**.
4. Click **Next** and a QR code will appear.

### Step 3: Scan the QR Code
1. Open Microsoft Authenticator on your phone.
2. Tap **+** (Add account) → **Work or school account** → **Scan QR code**.
3. Point your phone camera at the QR code on screen.
4. The account `company.com` will appear in the app.

### Step 4: Verify Setup
1. The portal will send a test notification to your phone.
2. Tap **Approve** in the Authenticator app.
3. Click **Done** in the portal. MFA is now active.

## Setting Up Google Authenticator

1. Install Google Authenticator from App Store or Google Play.
2. Go to `mfa.company.com` → **Add method** → **Authenticator app (TOTP)**.
3. Open Google Authenticator → **+** → **Scan QR code**.
4. Scan the QR code displayed in the portal.
5. Enter the 6-digit code shown in the app to verify.

## Using MFA Day-to-Day

### Push Notification (Microsoft Authenticator)
1. Sign in with username and password.
2. A push notification appears on your phone.
3. Tap **Approve**. You are signed in.

### TOTP Code (Google Authenticator / any TOTP app)
1. Sign in with username and password.
2. Open your authenticator app and copy the 6-digit code.
3. Enter the code in the sign-in prompt. Codes refresh every 30 seconds.

## Lost or New Phone

1. Go to `mfa.company.com` from a browser where you're still signed in.
2. Click **Manage authentication methods** → **Remove** the old device.
3. Set up MFA on your new phone using the steps above.

If you are completely locked out (cannot sign in at all):
- Contact IT Support with your employee ID for a temporary bypass code.
- Bring your employee badge to the IT desk for identity verification.

## Troubleshooting

### "I'm not receiving push notifications"
- Ensure the Authenticator app has notification permissions enabled.
- Check your phone's Do Not Disturb settings.
- Use a TOTP code manually instead: tap your account in the app to see the code.

### "Code is invalid or expired"
- Ensure your phone's time is synced automatically (Settings → Date & Time → Set Automatically).
- TOTP codes are only valid for 30 seconds; enter the code quickly after it refreshes.

### "I lost my phone and can't sign in"
- Call IT Support at ext. 4357 for an emergency bypass code.

## Contact
IT Support: `it-support@company.com` | Internal ext. 4357
