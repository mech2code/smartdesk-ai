# Software Installation Requests

## Overview
Employees may request software installation through the IT portal. Personal software or unlicensed applications are not permitted on company devices. All software must be approved by IT Security before installation.

## Approved Software Catalog
The following software is pre-approved and can be self-installed via **Software Center** (Windows) or **Self Service** (macOS):

| Software | Category | Self-Install |
|---|---|---|
| Microsoft 365 (Word, Excel, PowerPoint, Outlook, Teams) | Productivity | Yes |
| Slack | Communication | Yes |
| Zoom | Video conferencing | Yes |
| Google Chrome | Browser | Yes |
| Mozilla Firefox | Browser | Yes |
| Visual Studio Code | Development | Yes |
| Git | Development | Yes |
| Docker Desktop | Development | Yes |
| Adobe Acrobat Reader | PDF | Yes |
| 7-Zip / The Unarchiver | Utilities | Yes |
| VLC Media Player | Media | Yes |
| Cisco AnyConnect | VPN | Yes |

## Requesting New Software (Not in Catalog)

1. Go to `it-portal.internal/software-request`.
2. Fill in:
   - Software name and version
   - Business justification (why you need it)
   - Estimated number of users
   - Cost (if paid)
3. Submit the request.
4. IT Security reviews within **3 business days**.
5. If approved, IT will add it to the catalog or install it remotely.

## Approval Criteria
Requests are evaluated on:
- Security posture (no known vulnerabilities)
- Licensing compliance
- Business need
- Data privacy implications (especially cloud-based tools)

## Installing from Software Center (Windows)

1. Open the Start menu and search **Software Center**.
2. Browse or search for the application.
3. Click the application, then **Install**.
4. Installation runs in the background — no admin rights needed.
5. A notification confirms completion.

## Installing from Self Service (macOS)

1. Open **Self Service** from the Dock or Applications folder.
2. Find the application and click **Install**.
3. Enter your Mac login password if prompted.
4. The app will appear in Applications when done.

## Prohibited Software
The following are not permitted on company devices:
- Torrenting clients (BitTorrent, uTorrent)
- Unlicensed commercial software
- Personal VPN clients (use company VPN only)
- Cryptocurrency mining software
- Any software flagged by IT Security

Installing prohibited software may result in disciplinary action.

## Troubleshooting

### "Software Center / Self Service shows no applications"
- Ensure you are connected to the corporate network or VPN.
- Restart the Management Agent: search "Intune Management Agent" (Windows) or restart the Jamf agent (macOS).
- Contact IT if the issue persists.

### "Installation fails midway"
- Free up at least 5 GB of disk space and retry.
- Restart your computer and try again.
- Submit a helpdesk ticket with the error message.

### "I need software urgently (same day)"
- Email `it-support@company.com` with "URGENT" in the subject and your manager cc'd.
- IT will prioritize same-day review for business-critical requests.

## Contact
IT Support: `it-support@company.com` | IT Portal: `it-portal.internal`
