# GTA V Enhanced

**Status (2026-11-24):** gets past the DirectX 12 check and reaches the boot/legal screen. Gameplay not yet tested.

**Install tested:** Epic Games copy, installed through the Epic launcher inside a NotProton prefix and added to Steam as a non-Steam shortcut. Launched via `PlayGTAV.exe` (Epic sign-in → Rockstar Launcher → `GTA5_Enhanced.exe`). Pointing the shortcut at the Rockstar `Launcher.exe` also works, but then you press Play yourself.

## Launch options

```
CX_GRAPHICS_BACKEND=d3dmetal WINEMSYNC=1 NOTPROTON_RUNNER_VARIANT=gptk4b3-stock-d3d12 %command%
```

Needs the `gptk4b3-stock-d3d12` [runner variant](../../docs/runner-variants.md), which overlays the stock GPTK 4.0b3 `d3d12.dll`. It is only required if your runner's `d3d12.dll` is not the stock one. On an untouched GPTK 4.0b3 runner, the first two variables should be enough.

## Symptom

- Error `ERR_GFX_D3D_NOD3D12` / "DirectX 12 not supported", then the game exits.
- Wine log ends with `Unhandled exception code c0000409`.
- Changing `D3DM_*` launch options made no difference.

## Root cause

GTA V Enhanced is built on Microsoft's **Agility SDK 1.611**: the exe exports `D3D12SDKVersion = 611` and `D3D12SDKPath = .\D3D12-REDIST\`. Agility SDK games (and NVIDIA Streamline's `sl.interposer.dll`, which the game ships) call `D3D12GetInterface` from `d3d12.dll`.

The runner's `d3d12.dll` had been replaced by a custom wrapper for the [Forza Horizon 4 fix](../forza-horizon-4/README.md), and that wrapper does **not** export `D3D12GetInterface`. The stock GPTK file does. Without the export, the game concludes DX12 is unavailable.

D3DMetal itself was fine: GPTK 4.0b3's `d3d12core.dll` reports Agility SDK 619, newer than the 611 the game needs.

Forum reports that Enhanced "stopped working after a patch" fit this: the patch moved the game onto the Agility SDK.

## How it was found

| # | Checked | Evidence | Conclusion |
| --- | --- | --- | --- |
| 1 | Wine log after a failed launch | `Using the Vulkan renderer for d3d10/11`, `vkd3d: Cannot load DXIL conversion library`, then `c0000409` | Some process was not on D3DMetal. Not yet clear which. |
| 2 | Where `CX_GRAPHICS_BACKEND` is read | Strings in `lib/wine/x86_64-unix/cxcompatdb.so`: a per-exe hack database that can force a backend | CrossOver can override the env var per executable. |
| 3 | Traced the launch with `trace+cxcompatdb` | Rockstar `Launcher.exe` matched hack "Bug 23348" and was forced to wined3d | Explains the Vulkan/vkd3d lines, but only for the launcher. |
| 4 | Backend of `GTA5_Enhanced.exe` itself | `using d3dmetal as the graphics backend` | The game was on D3DMetal all along. |
| 5 | DLL loads in the game process | `D3D12.DLL` loaded and unloaded repeatedly; no `d3d12core.dll` | The game rejected the d3d12 it was given. |
| 6 | Hashes vs the GPTK 4.0b3 DMG | Every GPTK DLL matched except `d3d12.dll`, a custom wrapper (env vars `HB_TSSHIM_*`) left over from Forza work | Local modification found. |
| 7 | Exports of both `d3d12.dll` files | Stock exports `D3D12GetInterface`; the wrapper does not | The missing export is the cause. |
| 8 | Agility SDK versions | Game: 611. D3DMetal 4.0b3 `d3d12core.dll`: 619 | D3DMetal is new enough. |
| 9 | Retest with a variant carrying the stock `d3d12.dll` | Game loaded `d3d12core.dll`, no `c0000409`, reached the boot/legal screen | Fixed. |

## Not needed

The Rockstar Launcher being forced onto wined3d by CrossOver's compat database ("Bug 23348") is expected and harmless: it only affects the launcher's own window, not the game process.

## Sources

- [CodeWeavers forum: Enhanced broke after a patch, Agility SDK requirement](https://www.codeweavers.com/support/forums/general?msg=322566&t=27)
- [CodeWeavers forum: ERR_GFX_D3D_NOD3D12 report](https://www.codeweavers.com/support/forums/general?msg=328843&t=27)
- [Steam discussion: stopped working on Mac after an update](https://steamcommunity.com/app/3240220/discussions/0/669452940991277490)
