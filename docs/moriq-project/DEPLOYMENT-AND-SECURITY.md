# Installing, hosting and security testing

## Do we need a domain or a database?

|Setup|Domain|Database|Other needs|
|---|---|---|---|
|One person on one computer, as now|No|The built-in SQLite file is enough|None|
|A team, through one shared server|Yes, about USD 10 to 20 a year, with free HTTPS|SQLite can serve a small team on one server|A server, logins, access control, backups and a cloud model or GPU|
|A team on one private network|No, if a private network tool such as Tailscale is used|SQLite|Logins, backups and a model|
|Many users across several servers|Yes|PostgreSQL, because SQLite is a single file on one machine|The items above, plus monitoring|

Do not put the current version online. It has no login, so anyone who could reach it could read every saved chat.

## Which kind of app?

|Option|Works on|Needs|
|---|---|---|
|Installed web app, as built|Windows now. iPhone and Android once hosted over HTTPS|Hosting for phones|
|Native iPhone app in SwiftUI|iPhone, through the App Store|A Mac with Xcode, an Apple Developer account at USD 99 a year, a rewrite of the interface and App Review|
|Native Windows app with Tauri or Electron|Windows and Mac|A packaging toolchain, with little benefit over the installed web app|

Install on Windows by running `install-moriq.ps1` once, then use the MORIQ AI icon. The local server keeps running in the background after the window closes, until you sign out or end `pythonw.exe`.

## Security testing

`moriq/app/test_security.py` checks known risks: path traversal, requests from other websites, script injection, malformed input, attempts to leave the architecture scope, and hostile document titles. It does not replace a penetration test.

[Strix](https://github.com/usestrix/strix) is an AI penetration testing tool. It has not been run on this project, because it needs Docker running and a paid AI API key. It also consumes disk space that this computer lacks, and its usage costs money.

To run it later, on this app only:

1. Start Docker Desktop and install Strix using its current README. Read any install script before running it.
2. Set `STRIX_LLM` and `LLM_API_KEY` as its README describes.
3. Start the app with the scanner allowed: `$env:MORIQ_SCAN_HOST='host.docker.internal'; py -3.12 -m moriq.app`
4. Point Strix at `http://host.docker.internal:5180`, or at the `moriq/app` folder for a code scan.
5. Restart the app without `MORIQ_SCAN_HOST` afterwards.

Scan only systems you own or have written permission to test. The scan will send code and app behaviour to your chosen AI provider.
