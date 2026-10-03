# WSL2 Setup (Windows host)

The pipeline runs fine on Linux natively. On Windows, WSL2 gives the best toolchain
compatibility (Calibre + WeasyPrint + pandoc all install cleanly from apt). These are the
host-specific notes we learned the hard way.

## Distribution

- Ubuntu 24.04+ works. Keep the distro's `ext4.vhdx` on a secondary drive if C: is small:
  `wsl --manage Ubuntu --move D:\WSL\Ubuntu` (run `wsl --shutdown` first if you get
  `ERROR_SHARING_VIOLATION` right after a conversion — the service holds file handles).
- `wsl --set-default-version 2` so new distros are v2.

## Toolchain

```bash
sudo apt update
sudo apt install -y pandoc calibre weasyprint poppler-utils
```

`poppler-utils` gives you `pdfinfo`/`pdftotext`, used for page counts and text-sanity
sampling. Note: `apt install weasyprint` on recent Ubuntu pulls the correct Pango/cairo
stack automatically — installing WeasyPrint via pip on a bare system is the harder path.

## Passwordless sudo (automation convenience)

For agent-driven automation you do not want a sudo prompt mid-pipeline:

```bash
# from Windows: WSL allows entering as root without a password
wsl -d Ubuntu -u root -e bash -c "echo '<user> ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/<user> && chmod 440 /etc/sudoers.d/<user> && visudo -c -q"
```

This is equivalent in trust boundary to what you can already do via `wsl -u root` — it does
not weaken the WSL boundary (the Windows user controls the distro either way). Do not do
this on a shared/multi-user machine.

## Filesystem placement

- Keep the project and book temp dirs **inside the WSL filesystem** (`~/workspace/...`).
  Processing files directly from `/mnt/c/...` works but is 5–10× slower per I/O call, and a
  200-chunk pipeline multiplies the difference.
- Copy inputs in once (`cp /mnt/c/Users/.../book.epub ~/workspace/inputs/`), work in WSL,
  copy final PDFs out to the Windows drive at the end.
- **Copy `images/` with the temp directory.** Deriving a second temp dir without it produced
  a 604 KB PDF instead of 2.9 MB (all figures missing) — caught only by the size check.

## Known WSL2 quirks (cosmetic)

- `Failed to configure network (networkingMode Nat), falling back to networkingMode
  Consomme.` — harmless warning on some hosts; commands still succeed.
- `wsl.exe` output occasionally contains NUL bytes in captured stdout (UTF-16 artifacts).
  Strip them when parsing output from scripts; files inside WSL are unaffected.
- Hyper-V/Virtual Machine Platform: on stripped-down Windows builds (debloated ISOs), the
  VirtualMachinePlatform payload may be missing entirely and DISM downloads fail
  (`0x800f0950`). Enabling full Hyper-V from local WinSxS payload
  (`dism /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart` +
  reboot) was sufficient for WSL2 on a machine where the VMP payload was unrecoverable
  (regional CDN serving wrong TLS certificates). YMMV; the clean fix is a repair-install.

## Verifying the toolchain

```bash
python3 --version          # 3.10+
ebook-convert --version
pandoc --version
python3 -c "import weasyprint; print('weasyprint ok')"
pdfinfo -v 2>&1 | head -1  # poppler-utils
```
