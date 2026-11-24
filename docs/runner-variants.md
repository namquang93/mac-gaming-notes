# Per-game DLL changes with NotProton runner variants

A variant is a cheap APFS clone of the runner with your files overlaid, chosen per game by one launch option. Use it instead of editing the shared runner, because an edit made for one game silently changes every other game on that runner.

## Making one

1. **Make a source tree** whose top folders mirror the destination inside the runner. For a GPTK DLL the destination is `lib64/apple_gptk/wine`, so the tree holds `x86_64-windows/<file>.dll`:

   ```sh
   NP=~/Library/Application\ Support/notproton
   mkdir -p "$NP/variant-src/gptk4b3-stock-d3d12/x86_64-windows" "$NP/variants"
   cp "/Volumes/Evaluation environment for Windows games 4.0 beta 3/redist/lib/wine/x86_64-windows/d3d12.dll" \
      "$NP/variant-src/gptk4b3-stock-d3d12/x86_64-windows/"
   ```

2. **Write a descriptor**, `~/Library/Application Support/notproton/variants/<id>.conf`:

   ```ini
   [gptk4b3-stock-d3d12]
   label = GPTK 4.0b3 stock d3d12
   src = ~/Library/Application Support/notproton/variant-src/gptk4b3-stock-d3d12
   dst = lib64/apple_gptk/wine
   ```

3. **Select it per game:** add `NOTPROTON_RUNNER_VARIANT=<id>` before `%command%` in the game's Steam launch options. Join several variants with `+`.
4. **Launch once.** The run log should say:

   ```
   === variants: built crossover-<build>+<id>@<hash> ===
   runner: variant asked for <id>, using <id>
   ```

## Rules the run script enforces

- Fields allowed: `label`, `variant`, `src`, `dst`, `build` (up to 8), `remove` (up to 32). `src` and `dst` are required; unknown fields are refused.
- Ids are letters, digits, `.`, `_` and `-`, at most 64 characters.
- `src` may be absolute or start with `~/`; anything else is taken relative to `$HOME`.
- `remove = <path>` deletes a file from the clone (path relative to `dst`).
- Replacing a file Wine itself ships (under `bin/`, `lib/wine/`, `share/wine/`) requires `build = <runner build>`, e.g. `build = 26.3.0.39832`. GPTK and DXMT folders don't.
- `ntdll` and `lsteamclient` are refused, because they carry NotProton's Steam bridge.
- A DLL name the base runner never had is copied into the prefix's `system32` automatically, so forwards to it resolve.
- Set `NOTPROTON_VARIANT_REBUILD=1` for one launch to force a rebuild after changing the source files.
- Refusals are logged as `=== variants: … ===` in the run log.
