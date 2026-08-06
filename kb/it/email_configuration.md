# Corporate Email Configuration Guide

## Overview
Company email is powered by Microsoft 365 (Outlook). Your corporate email address is `firstname.lastname@company.com`. This guide covers setup on desktop, mobile, and web.

## Accessing Email

### Web (No Setup Required)
Go to `mail.company.com` and sign in with your corporate credentials + MFA.

### Desktop — Outlook (Windows/macOS)
Outlook is pre-installed on all company laptops. On first launch:
1. Open Outlook.
2. Enter your corporate email: `firstname.lastname@company.com`.
3. Click **Continue** / **Next**.
4. Sign in with your corporate password and MFA.
5. Outlook auto-configures Exchange settings — no manual server entry needed.
6. Click **Done**. Your mailbox will sync within a few minutes.

### Mobile — Outlook App (iOS / Android)

1. Install **Microsoft Outlook** from App Store or Google Play.
2. Open the app and tap **Add Account**.
3. Enter your corporate email address.
4. Tap **Continue** — the app detects company settings automatically.
5. Sign in with your corporate password and MFA.
6. Tap **Maybe Later** when asked to add another account.
7. Your inbox will sync within a few minutes.

## Email Settings Reference

| Setting | Value |
|---|---|
| Server type | Microsoft Exchange / Microsoft 365 |
| Incoming server | `outlook.office365.com` |
| Outgoing server | `smtp.office365.com` |
| SMTP port | 587 (TLS) |
| IMAP port | 993 (SSL) |
| Username | Full email address (`firstname.lastname@company.com`) |

Use these settings only if configuring a third-party email client (Thunderbird, Apple Mail, etc.).

## Mailbox Limits
| Item | Limit |
|---|---|
| Mailbox size | 100 GB |
| Single attachment | 35 MB |
| Email retention | 7 years (compliance hold) |

## Distribution Lists and Shared Mailboxes

### Requesting Access to a Shared Mailbox
1. Submit a request at `it-portal.internal/mailbox-access`.
2. Your manager must approve.
3. Access is granted within 1 business day.

### Joining a Distribution List
Email `it-support@company.com` with the list name and your business reason.

## Email Signature

Your corporate signature must include:
- Full name and job title
- Department
- Phone number (direct line or ext.)
- Company logo (download from `it-portal.internal/assets`)

Template is available at `it-portal.internal/signature-template`.

## Spam and Phishing

- Suspicious emails are automatically quarantined. Check `quarantine.company.com` for false positives.
- Report phishing: Forward to `phishing@company.com` or use the **Report Phishing** button in Outlook.
- Never click links or download attachments from unknown senders.

## Out of Office

1. In Outlook: **File → Automatic Replies** (Windows) or **Tools → Out of Office** (macOS).
2. Set your dates and message.
3. Configure a separate message for internal vs. external senders.

## Troubleshooting

### "Cannot connect to Exchange / Mailbox unavailable"
- Check your internet or VPN connection.
- Go to `status.company.com` to check for service outages.
- Try signing out and back into Outlook.

### "Email not syncing on mobile"
- Ensure the Outlook app has Background App Refresh enabled.
- Remove and re-add the account in the app.

### "Outlook keeps asking for my password"
- Your corporate password may have expired. Reset at `accounts.company.com/reset`.
- Re-authenticate in the Microsoft 365 portal at `portal.office.com`.

### "Cannot send emails — over quota"
- Delete old emails and empty the Deleted Items and Junk folders.
- Archive old emails using Outlook's Archive feature.

## Contact
IT Support: `it-support@company.com` | Internal ext. 4357
