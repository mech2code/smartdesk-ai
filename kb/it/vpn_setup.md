# VPN Setup Guide — Cisco AnyConnect

## Overview
All remote employees must use the company-approved VPN client, Cisco AnyConnect, to securely access internal systems. VPN is mandatory when working outside the office.

## Prerequisites
- Company-issued laptop or approved personal device
- Active employee account credentials (username + password)
- Enrolled in MFA (required for VPN access)

## Installation

### Windows
1. Open the Software Center from the Start menu.
2. Search for "Cisco AnyConnect Secure Mobility Client".
3. Click Install and wait for completion (approximately 5 minutes).
4. Launch AnyConnect from the Start menu or system tray.

### macOS
1. Open Self Service from the Dock or Applications folder.
2. Search for "Cisco AnyConnect".
3. Click Install. You may be prompted for your Mac login password.
4. After installation, open AnyConnect from the Applications folder.

### Linux
1. Download the AnyConnect installer from the IT portal at `it-portal.internal/downloads`.
2. Run: `sudo ./anyconnect-linux64-*.sh`
3. Accept the license agreement and complete the installation.

## Connecting to VPN

1. Open Cisco AnyConnect.
2. In the connection field, enter: `vpn.company.com`
3. Click Connect.
4. Enter your **corporate username** (e.g., `jdoe`) and **corporate password**.
5. When prompted for MFA, open your authenticator app and enter the 6-digit code.
6. Click OK. You are now connected.

## Disconnecting
Click the AnyConnect icon in the taskbar/menu bar and select Disconnect.

## Troubleshooting

### "Unable to connect to server"
- Confirm you are using `vpn.company.com` (not a personal VPN address).
- Check your internet connection independently (try loading a public website).
- Restart AnyConnect and try again.
- If the issue persists, restart your computer.

### "Authentication failed"
- Verify your username does not include the domain prefix (use `jdoe`, not `CORP\jdoe`).
- Ensure your password has not expired. Reset at `accounts.company.com/reset`.
- Confirm your MFA is set up correctly (see MFA Setup Guide).

### "Certificate error" or "Untrusted server"
- Do not proceed if you see this on a company network — contact IT immediately.
- On a home network, this may indicate a DNS issue; try restarting your router.

### Slow connection over VPN
- Use split-tunnel when instructed by your manager (IT must enable per request).
- Avoid large file transfers over VPN; use SharePoint/OneDrive instead.

## VPN Access Levels
| Role | Access Level |
|---|---|
| Standard employee | Internal intranet, email, collaboration tools |
| Developer | Above + dev/staging environments |
| IT Admin | Full network access |

## Supported Platforms
- Windows 10/11
- macOS 12 Monterey and later
- Ubuntu 20.04 / 22.04 LTS

## Contact
For VPN issues not resolved by this guide, submit a ticket via the IT helpdesk portal or contact IT Support at `it-support@company.com`.
