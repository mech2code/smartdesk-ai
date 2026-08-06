# Wi-Fi Access Guide

## Overview
The company provides two wireless networks: a secure corporate network for employees and a guest network for visitors and contractors. Both require specific credentials.

## Available Networks

| Network Name (SSID) | Who Can Use | Authentication |
|---|---|---|
| `CORP-SECURE` | All employees | Corporate credentials + MFA |
| `CORP-GUEST` | Visitors, contractors, personal devices | Self-registration portal |
| `CORP-IOT` | IT-managed devices only | Certificate-based (IT managed) |

## Connecting to CORP-SECURE (Employee Network)

### Windows
1. Click the Wi-Fi icon in the system tray.
2. Select **CORP-SECURE** from the list.
3. Click **Connect**.
4. When prompted, enter:
   - Username: your corporate username (e.g., `jdoe`)
   - Password: your corporate password
5. Complete MFA if prompted.
6. Windows may show a certificate warning — click **Connect** only if on company premises.

### macOS
1. Click the Wi-Fi icon in the menu bar.
2. Select **CORP-SECURE**.
3. Enter your corporate username and password.
4. If prompted to verify a certificate, click **Continue**.
5. Complete MFA if prompted.

### After a Password Reset
You must reconnect to CORP-SECURE after changing your password:
1. Forget the network (right-click → Forget / System Preferences → Forget).
2. Reconnect with your new password.

## Connecting to CORP-GUEST (Visitor / Personal Device)

CORP-GUEST provides internet access only — no access to internal systems.

1. Select **CORP-GUEST** from available Wi-Fi networks.
2. Open a browser. You will be redirected to the guest portal.
3. Choose one of:
   - **Employee sponsor**: Enter your corporate email, and your guest will receive an SMS/email code.
   - **Self-registration**: Enter name, email, and reason for visit. IT approves within 15 minutes during business hours.
4. Once approved, the device receives a session passcode (valid for 8 hours / 1 day for contractors).

### Sponsoring a Guest
1. Go to `wifi-portal.internal/sponsor`.
2. Enter the guest's name and email/phone.
3. Select duration (1 day, 1 week, or custom for contractors).
4. Click **Create**. The guest receives their access code automatically.

## Wi-Fi Coverage Map
Full coverage is available in:
- All office floors and conference rooms
- Cafeteria and common areas
- Parking garage (limited — ground floor only)

Dead zones: stairwells, server room, basement storage. Contact IT to report persistent coverage issues.

## Troubleshooting

### "CORP-SECURE not visible in Wi-Fi list"
- Ensure Wi-Fi is enabled.
- Move closer to a wireless access point.
- Check if your device's Wi-Fi adapter driver is up to date.

### "Authentication failed on CORP-SECURE"
- Verify your corporate password is not expired (`accounts.company.com/reset`).
- Forget the network and reconnect.
- Ensure your device clock is correct (certificate validation requires accurate time).

### "Connected to CORP-SECURE but no internet"
- Confirm VPN (AnyConnect) is not interfering — disconnect VPN, then reconnect Wi-Fi.
- Flush DNS: `ipconfig /flushdns` (Windows) or `sudo dscacheutil -flushcache` (macOS).
- Submit a ticket if the issue persists across devices.

### "CORP-GUEST portal not loading"
- Ensure you're connected to CORP-GUEST (not CORP-SECURE or a personal hotspot).
- Disable any browser extensions or ad blockers temporarily.
- Try opening `http://wifi-portal.internal` directly.

### "Guest access expired mid-day"
- Employee sponsors can extend access at `wifi-portal.internal/sponsor`.
- Guest can re-register at the portal for a new session code.

## Security Policy
- Do not share your CORP-SECURE credentials with guests or personal devices.
- CORP-GUEST traffic is monitored and logged per company policy.
- Unauthorized access to CORP-SECURE is a policy violation.

## Contact
IT Support: `it-support@company.com` | Internal ext. 4357 | Wi-Fi Portal: `wifi-portal.internal`
