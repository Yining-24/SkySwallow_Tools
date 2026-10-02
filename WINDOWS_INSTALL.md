# Windows installer preview

The GitHub Actions **Build Windows package** workflow produces both a portable ZIP
and `SkySwallowTools-Setup-windows-x64.exe`. The installer is the file to use for
the next Windows test.

1. Stop any running `SkySwallowServer.exe` window with **Ctrl+C**.
2. Run the installer as a Windows administrator.
3. At first-time setup, choose **No** for local-network access on a test PC.
   Choose **Yes** only when installing on the company host.
4. Enter three different passwords of at least 12 characters for Administrator,
   Finance, and Follow-up staff. Password input is hidden.
5. Open **Start SkySwallow Tools** from the Start menu. Keep its console window
   open while using the app.
6. On the same PC, open `http://127.0.0.1:5001/` and sign in.

The installer saves a random Flask secret and password hashes in
`C:\ProgramData\SkySwallowTools\config.py`. It preserves an existing config on
upgrade and uninstall. If a config already exists, first-time setup asks you
to type `REUSE` before using it. For safety, it refuses existing folders or
files with unfamiliar ownership or permissions; have an administrator review
those instead of overriding the warning. The setup restricts the configuration
folder to the installing Windows account, Administrators, and SYSTEM. Run the
server from the same Windows account used to install it. Never put `config.py` in
GitHub or send it to another person.

This installer preview does not set up automatic startup or a Windows Firewall
rule. Those are required before the company host can serve other computers.
The financial upload and download flows also need a final real-Windows check
with a non-sensitive sample workbook before company use.
