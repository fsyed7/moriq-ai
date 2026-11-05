# Installing, hosting and security testing

## Do we need a domain or a database?

|Setup|Domain|Database|Other needs|
|---|---|---|---|
|One person on one computer, as now|No|The built-in SQLite file is enough|None|
|A team, through one shared server|Yes, about USD 10 to 20 a year, with free HTTPS|SQLite can serve a small team on one server|A server, logins, access control, backups and a cloud model or GPU|
|A team on one private network|No, if a private network tool such as Tailscale is used|SQLite|Logins, backups and a model|
|Many users across several servers|Yes|PostgreSQL, because SQLite is a single file on one machine|The items above, plus monitoring|

Logins now exist, so the app can be hosted for a team using the steps below. Do not expose it without HTTPS, because passwords and chats would travel unencrypted.

## Which kind of app?

|Option|Works on|Needs|
|---|---|---|
|Installed web app, as built|Windows now. iPhone and Android once hosted over HTTPS|Hosting for phones|
|Native iPhone app in SwiftUI|iPhone, through the App Store|A Mac with Xcode, an Apple Developer account at USD 99 a year, a rewrite of the interface and App Review|
|Native Windows app with Tauri or Electron|Windows and Mac|A packaging toolchain, with little benefit over the installed web app|

Install on Windows by running `install-moriq.ps1` once, then use the MORIQ AI icon. The local server keeps running in the background after the window closes, until you sign out or end `pythonw.exe`.

## Accounts

The first person to open the app creates the admin account. The admin adds people from the account button in the sidebar, and each person gets a temporary password to change when they first sign in.

- Passwords are stored as salted scrypt hashes, and sign-in tokens only as SHA-256 hashes.
- Sign-in lasts 14 days. Cookies are `HttpOnly` and `SameSite=Strict`, and also `Secure` when hosted.
- Eight wrong passwords lock that username for 15 minutes, and 40 from one address lock that address.
- Each person sees only their own chats. Admins cannot read other people's chats in the app, but whoever runs the server can open the database.
- Questions wait in a queue, for up to three minutes, because a CPU-only machine answers one at a time.

Whoever runs the server can use these from the repository root:

```shell
py -3.12 -m moriq.app.admin list
py -3.12 -m moriq.app.admin reset-password USERNAME
py -3.12 -m moriq.app.admin activity
py -3.12 -m moriq.app.admin backup moriq-backup.sqlite3
```

This protects one small team on one server. It has no multi-factor sign-in, single sign-on or email recovery, and the activity log can be edited by anyone with access to the database.

## Hosting for a team

These steps have not yet been run on a real server. The hosted settings are covered by tests only.

1. Get a Linux server and a domain, and point the domain at the server. Answers need about 8 GB of memory for the local model, and they will be slow without a GPU.
2. Install Python 3.12, Ollama with the model named in `moriq/app/provider.py`, and [Caddy](https://caddyserver.com).
3. Copy this repository to `/opt/moriq-ai`, and create a `moriq` user that owns `/var/lib/moriq`.
4. Copy the files from `deploy/`, and replace the example domain in `Caddyfile` and `moriq.env.example`.
5. Start the service. On first run it writes a one-time setup code to `/var/lib/moriq/setup-code.txt`, so a stranger cannot claim the admin account. Enter that code on the setup screen.
6. Schedule the backup command and copy the backups off the server.
7. Keep only ports 80 and 443 open, and leave Ollama and port 5180 private.

The app listens on 127.0.0.1 only, so the reverse proxy is the only way in.

## Security testing

`moriq/app/test_auth.py` and `moriq/app/test_security.py` check known risks: account takeover, access to other people's chats, password guessing, path traversal, requests from other websites, script injection, malformed input, attempts to leave the architecture scope, and hostile document titles. It does not replace a penetration test.

[Strix](https://github.com/usestrix/strix) is an AI penetration testing tool. It has not been run on this project, because it needs Docker running and a paid AI API key. It also consumes disk space that this computer lacks, and its usage costs money.

To run it later, on this app only:

1. Start Docker Desktop and install Strix using its current README. Read any install script before running it.
2. Set `STRIX_LLM` and `LLM_API_KEY` as its README describes.
3. Start the app with the scanner allowed: `$env:MORIQ_SCAN_HOST='host.docker.internal'; py -3.12 -m moriq.app`
4. Point Strix at `http://host.docker.internal:5180`, or at the `moriq/app` folder for a code scan.
5. Restart the app without `MORIQ_SCAN_HOST` afterwards.

Scan only systems you own or have written permission to test. The scan will send code and app behaviour to your chosen AI provider.
