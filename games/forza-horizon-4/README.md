# Forza Horizon 4

**Status (2026-11-22):** launches and drives in free roam (last session ran healthy). Online is unreliable, as the patches repo itself warns.

**Install:** Steam copy (app id `1293830`), run through NotProton (not a CrossOver bottle), with the community patches from [whyAm-i/Forza-Horizon-4-patches-for-mac](https://github.com/whyAm-i/Forza-Horizon-4-patches-for-mac).

> This page was rebuilt from notes kept during the original setup (late Oct to early Nov 2026) and checked against the files installed now. It is not a full log of every step.

## Launch options

```
CX_GRAPHICS_BACKEND=d3dmetal WINEMSYNC=1 D3DM_MTL4=0 D3DM_ENABLE_METALFX=0 D3DM_VENDOR_ID=0x8086 D3DM_DEVICE_ID=0x56a1 %command%
```

- `CX_GRAPHICS_BACKEND=d3dmetal` must come from launch options. NotProton has no `cxbottle.conf`.
- **The GPU id spoof (`D3DM_VENDOR_ID` / `D3DM_DEVICE_ID`, an Intel Arc A770) is required.** Without it the game crashes at startup inside `ucrtbase` (`sscanf("%d.%d.%d")` on a NULL string), apparently while parsing a GPU driver version.
- Keep `%command%` at the end. Without it, NotProton passes the variables to the game as arguments.

## What the patches repo assumes vs what NotProton needs

The repo's install guide targets a CrossOver bottle named "Steam". Under NotProton the same files go to different places:

| Repo says | Under NotProton |
| --- | --- |
| `$CX` = `/Applications/CrossOver.app/.../CrossOver` | The NotProton runner: `~/Library/Application Support/notproton/runners/crossover-26.3.0.39832/CrossOver` |
| `$BOTTLE` = `~/Library/Application Support/CrossOver/Bottles/Steam` | The prefix: `~/Library/Application Support/Steam/steamapps/compatdata/1293830/pfx` |
| `HB_*` variables in `cxbottle.conf` | Prefix registry, `HKCU\Environment` (see below) |
| `CX_GRAPHICS_BACKEND` in `cxbottle.conf` | Steam launch options |

The CrossOver version must still match: the runner is CrossOver 26.3 build `26.3.0.39832`, which is what the patches were built against.

## What is installed

| File | Where | SHA-256 (prefix) | What it is |
| --- | --- | --- | --- |
| `kernelbase.dll` | runner `lib/wine/x86_64-windows/` and prefix `system32/` | `313a9d07…` | Repo patch 01: fakes the UWP package query that otherwise loops forever at launch |
| `kernel32.dll` | runner | stock | Leave it stock (see pitfalls) |
| `lib64/apple_gptk/` | runner | GPTK 4.0b3 | D3DMetal swapped from CrossOver's 3.0 to Apple GPTK 4.0 beta 3. Originals kept as `external.old` and `wine.old` |
| `d3d12.dll` | runner `lib64/apple_gptk/wine/x86_64-windows/` and prefix `system32/` | `833b9642…` | Repo patch 02 shim, "drift-zone V3" build (vertex-offset fix, open-world crash handler, drift-zone fix) |
| `apd12.dll` | same two places | `32c942ed…` | The real GPTK 4.0b3 `d3d12.dll`, renamed so the shim can load it (`HB_D3D12_REAL=apd12.dll`) |
| `apd12.so` | runner `lib64/apple_gptk/wine/x86_64-unix/` | symlink | `→ ../../external/libd3dshared.dylib`, so the renamed provider still reaches D3DMetal |
| `TargetHardwareProfiler.dll` | game folder | renamed to `.disabled` | Crashes at the splash screen (WMI hardware probe) |

`apd12.dll` is GPTK 4.0b3's `d3d12.dll` with its internal export name changed to `apd12.dll`. Its hash matches the provider the patches repo was tested with.

The repo has since published newer shims (memory-leak repair V1.1, `f3038fdc…`, and online fixes). This machine still runs drift-zone V3. Use the repo's `09-memory-leak/install.py` to upgrade.

## Shim settings (`HKCU\Environment` in the prefix)

| Variable | Value |
| --- | --- |
| `HB_D3D12_REAL` | `apd12.dll` |
| `HB_TSSHIM_EXPLICIT_INPUT_OFFSETS` | `1` |
| `HB_TSSHIM_FIX_WORLD_ENTRY` | `1` |
| `HB_TSSHIM_CAPTURE_BINDINGS` | `0` |
| `HB_TSSHIM_CAPTURE_INDIRECT_ARGS` | `0` |
| `HB_TSSHIM_SKIP_ALL_INSTANCED` | `0` |

Set them with the runner's Wine loader directly. CrossOver's `bin/wine` wrapper ignores `WINEPREFIX`:

```sh
R=~/Library/Application\ Support/notproton/runners/crossover-26.3.0.39832/CrossOver
export WINEPREFIX=~/Library/Application\ Support/Steam/steamapps/compatdata/1293830/pfx
"$R/lib/wine/x86_64-unix/wine" reg add 'HKCU\Environment' /v HB_D3D12_REAL /d apd12.dll /f
"$R/lib/wine/x86_64-unix/wine" reg add 'HKCU\Environment' /v HB_TSSHIM_EXPLICIT_INPUT_OFFSETS /d 1 /f
"$R/lib/wine/x86_64-unix/wine" reg add 'HKCU\Environment' /v HB_TSSHIM_FIX_WORLD_ENTRY /d 1 /f
```

Never leave `HB_TSSHIM_DEBUG=1` set: its logs fill the disk quickly.

## Pitfalls

- **Keep `kernel32.dll` stock.** A custom `GetPackagePath` export got past an early `0x8FF` crash but caused a hang in `steamclient64.dll`. The working state uses the original `kernel32.dll` plus the patched `kernelbase.dll`.
- **Reinstalling FH4 in Steam recreates the prefix.** That wipes the prefix's `d3d12.dll`, `apd12.dll` and the `HB_*` registry values, and restores `TargetHardwareProfiler.dll`. Redo all three. `kernelbase.dll` comes back patched from the runner.
- **A NotProton runner update can replace the runner files** (`kernelbase.dll`, `lib64/apple_gptk/`). Re-check the hashes above after updating.
- **A crash at the splash that looks like a network crash** (read of `0x18`, near `MSWSOCK`) is `TargetHardwareProfiler.dll`. Rename it again.
- **Online:** a crash at `0x143F4A5A4` (`network_party` / `create_party` in `AppData/Local/ForzaHorizon4/scratch/CrashReport.xml`) happened when the game went online. Workaround: turn Wi-Fi off after signing in. Newer repo builds include online fixes that were not tried here.
- **Wine traces** from `WINEDEBUG=` in launch options land in `notproton/launchers/1293830/notproton-wine.log`, not in `notproton-run.log`.

## Side effect on every other DX12 game

The shim was installed in the **shared runner**, so every game using that runner gets it as its `d3d12.dll`. The shim is not inert for other games: by default it registers FH4's world-entry crash handler, drops MSAA depth resolves, patches shader-model feature checks, and it does not export `D3D12GetInterface`.

Seen so far:

- **GTA V Enhanced** refused to start ("no DX12") because of the missing export. Fixed with a [runner variant](../../docs/runner-variants.md) carrying the stock `d3d12.dll`; see [its page](../gta-v-enhanced/README.md).
- **Black Myth: Wukong** ran only after adding `HB_D3D12_REAL=apd12.dll` to its launch options and copying `apd12.dll` into its own prefix's `system32` (the shim can't find it via `WINEDLLPATH`). Without that: Unreal's "Failed to choose a D3D12 Adapter". The ground was invisible; the shim, GPTK 4.0b or Unreal's DX12 path are all suspects.

**Cleaner layout (not applied yet):** put the stock GPTK `d3d12.dll` back in the shared runner and give FH4 the shim through its own runner variant (or only in FH4's prefix). Then other games need no workarounds, and GTA would not need its variant.
