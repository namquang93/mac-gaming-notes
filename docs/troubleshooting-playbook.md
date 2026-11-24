# Troubleshooting playbook

Work from the outside in: confirm what the game process actually got before changing any setting. Background on the pieces is in [how the stack works](how-the-stack-works.md).

## Checklist

1. **Find the right prefix and logs.** For a non-Steam shortcut the app id is the shortcut's id (a large number), not the store's id. Open `<compatdata>/<appid>/notproton-run.log` and `notproton/launchers/<appid>/notproton-wine.log`.
2. **Check the launch options arrived.** `notproton.log` prints the exact command Steam handed over (`[launch] handed to /bin/sh -c: …`). The run log prints lines like `sync: WINEMSYNC=1 from environment` and `runner: …`.
3. **Find which process is the game.** Wine thread ids are global. Match the id in `Loaded L"…\Game.exe"` (from `+loaddll`) or `started process pid X tid Y` (from `+process`) to the error lines.
4. **Check the graphics backend per process.** Run with `WINEDEBUG=trace+cxcompatdb,trace+process`. Each process logs `using <backend> as the graphics backend`, plus `applying hack "<name>"` when CrossOver's compat database overrides your choice.
   - Vulkan/vkd3d lines in a process mean that process is **not** on D3DMetal.
   - A compat hack on a launcher (e.g. the Rockstar Launcher) is normal and does not affect the game process.
5. **Watch what the game does with d3d12.** With `+loaddll`, a game that loads `D3D12.DLL` and immediately unloads it, several times, is probing DX12 and rejecting what it found.
6. **Compare DLLs against the stock files.** Hash the runner's `lib64/apple_gptk/wine/x86_64-windows/*.dll` against the GPTK DMG's `redist/lib/wine/x86_64-windows/`. A mismatch is a local modification, so list its exports with `objdump -p`.
7. **Check the Agility SDK requirement.** Agility SDK games export `D3D12SDKVersion` and `D3D12SDKPath`. Compare the game's version with the `D3D12SDKVersion` exported by D3DMetal's `d3d12core.dll` (use [`tools/rva.py`](../tools/rva.py)). D3DMetal must be equal or newer.
8. **Fix per game, not globally.** Put the different DLL in a [runner variant](runner-variants.md), then retest with `+loaddll`. Success looks like `d3d12core.dll` loading in the game process and no `c0000409`.

## Command cheat sheet

Set these once per shell. Replace `APPID` with the game's id (for a non-Steam shortcut, the shortcut's id from `steamapps/compatdata/`).

```sh
APPID=3147942017
NP=~/Library/Application\ Support/notproton
PFX=~/Library/Application\ Support/Steam/steamapps/compatdata/$APPID
R="$NP/runners/crossover-26.3.0.39832/CrossOver"
WLOG="$NP/launchers/$APPID/notproton-wine.log"
```

### Read the logs

```sh
tail -80 "$PFX/notproton-run.log"                        # env, runner, variant, exit status
grep -n -i -E "backend|HACK|vkd3d|wined3d|c0000409" "$WLOG"
grep -a "handed to" "$NP/notproton.log" | tail -5         # exact launch command Steam passed
```

### Trace one launch without Steam

Or add `WINEDEBUG=...` to the game's Steam launch options instead. Close Steam's copy of the game first; if the log says `Server is running with WINEMSYNC`, add `WINEMSYNC=1`.

```sh
CX_HOME=~/Library/Application\ Support/CrossOver CX_ROOT="$R" WINEPREFIX="$PFX/pfx" \
WINEDLLPATH="$R/lib/wine/x86_64-windows:$R/lib/wine/x86_64-unix" \
CX_GRAPHICS_BACKEND=d3dmetal WINEMSYNC=1 \
WINEDEBUG="trace+cxcompatdb,trace+process,+loaddll" \
"$R/lib/wine/x86_64-unix/wine" 'C:\Program Files\...\Game.exe' > /tmp/trace.log 2>&1

grep -a -E "applying hack|set_graphics_backend|CreateProcessInternalW app" /tmp/trace.log
grep -a -i -E "loaddll.*(d3d12|dxgi|d3d11)" /tmp/trace.log
"$R/bin/wineserver" -k                                    # stop everything in that prefix
```

To test exactly what Steam would run (including variants), call NotProton's `run` script directly with Steam's environment. Copy the variables from the top of `notproton-run.log`, the important ones being `STEAM_COMPAT_DATA_PATH`, `STEAM_COMPAT_CLIENT_INSTALL_PATH`, `STEAM_COMPAT_INSTALL_PATH`, `STEAM_COMPAT_TOOL_PATHS` and `SteamAppId`:

```sh
env STEAM_COMPAT_DATA_PATH="$PFX" STEAM_COMPAT_APP_ID=0 SteamAppId=$APPID ... \
  CX_GRAPHICS_BACKEND=d3dmetal WINEMSYNC=1 NOTPROTON_RUNNER_VARIANT=<id> \
  ~/Library/Application\ Support/Steam/compatibilitytools.d/notproton-26.3/run waitforexitandrun "<path to exe>"
```

### Compare GPTK DLLs with the DMG

```sh
V="/Volumes/Evaluation environment for Windows games 4.0 beta 3/redist/lib/wine/x86_64-windows"
D="$R/lib64/apple_gptk/wine/x86_64-windows"
for f in "$V"/*.dll; do b=$(basename "$f"); cmp -s "$f" "$D/$b" && echo "$b same" || echo "$b DIFFERENT"; done
objdump -p "$D/d3d12.dll" | sed -n '/Export Table/,/^$/p'
```

### Read a game's Agility SDK version

```sh
objdump -p Game.exe | grep -A4 "Export Table"     # shows D3D12SDKVersion and its RVA
python3 tools/rva.py Game.exe <rva-without-0x>     # prints the value, e.g. 611
```

## Pitfalls

- **Launch options copied from another game can be red herrings.** Flags like `D3DM_MTL4`, `D3DM_ENABLE_METALFX` or a GPU id spoof (`D3DM_VENDOR_ID` / `D3DM_DEVICE_ID`) fix one game and do nothing for another.
- **A shared-runner edit is a global edit.** Replacing a DLL in the runner for one game changes every game on that runner, and the breakage can show up weeks later.
- **Keep originals next to replaced files** (e.g. `d3d12.<version>-original.dll`, `external.old`). It turns the comparison into a one-line hash check.
- **The env var is only a request.** CrossOver's compat database can override `CX_GRAPHICS_BACKEND` per exe. Check `trace+cxcompatdb` before assuming the backend.
- **Launcher processes pollute the log.** Vulkan/vkd3d errors from a launcher look like the game's failure. Tie log lines to a process id first.
- **Running Wine from Terminal triggers macOS privacy prompts** (microphone, screen recording) attributed to Terminal. Deny them; they are not needed.
