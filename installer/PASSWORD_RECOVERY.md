# Set one shared six-digit PIN

Login remains enabled. All three roles use the same six-digit PIN, chosen on the
Windows computer. No preset PIN is supplied or saved in source code.

Anyone who knows this shared PIN can select Administrator and access every tool;
role selection no longer separates who can access financial tools. Keep the app
on the intended internal network, not exposed to the internet. Login attempts are
limited to five per minute per client address.

## Update an existing installation

1. Stop the server with Ctrl+C in its black window.
2. Install the latest update. When setup finds the existing configuration, type
   `PIN` to replace the passwords for all three roles.
3. Enter your own six-digit PIN twice. Characters are hidden while typing.
4. Wait for **Shared PIN updated for ALL three roles**.
5. Launch **Start SkySwallow Tools** and open `http://127.0.0.1:5001`.
   Select any role and enter the same PIN. To use the financial tools, select
   管理员 (Administrator) or 财务 (Finance).

Typing `REUSE` during an update preserves the old passwords instead. To change
them afterwards, search Windows Start for **Set SkySwallow Shared PIN**, right-click
it, choose **Run as administrator**, then type `PIN` and enter the new PIN twice.

PIN changes preserve the Flask secret, network address, port, and other settings.
A uniquely named private backup containing the old password hashes is retained
in the configuration directory. No plain-text PINs are saved. Existing active
browser sessions are not revoked; restart the server to use the new credentials.

Advanced usage, from an elevated terminal:

```powershell
& "C:\Program Files\SkySwallow Tools\SkySwallowServer.exe" --set-shared-pin
```
