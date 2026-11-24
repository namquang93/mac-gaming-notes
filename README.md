# mac-gaming-notes

Notes from getting Windows games running on Apple Silicon through **Mac Steam + [NotProton](https://github.com/NotProtonNot/NotProton)** (CrossOver runner) with **Apple's Game Porting Toolkit (D3DMetal)**. The goal is to be able to fix the next broken game without starting from zero.

## Setup these notes were written on

| | |
| --- | --- |
| Mac | M1 Max, macOS 26 |
| Launcher | Mac Steam with NotProton compat tool `notproton-26.3` (Rosetta flavor) |
| Runner | CrossOver 26.3 (`26.3.0.39832`) |
| D3DMetal | Game Porting Toolkit 4.0 beta 3, swapped into the runner's `lib64/apple_gptk/` |

## Games

| Game | Status | Notes |
| --- | --- | --- |
| [Forza Horizon 4](games/forza-horizon-4/README.md) | Free roam works; online unreliable | Community patches adapted to NotProton, GPU id spoof, GPTK 4.0b3 |
| [GTA V Enhanced](games/gta-v-enhanced/README.md) | Boots past the DX12 check (gameplay not yet tested) | Needs the stock GPTK `d3d12.dll` via a runner variant |

## Docs

- [How the stack works](docs/how-the-stack-works.md): Steam → NotProton → Wine → cxcompatdb → D3DMetal, and where every file and log lives.
- [Troubleshooting playbook](docs/troubleshooting-playbook.md): the step-by-step checklist and command cheat sheet.
- [Runner variants](docs/runner-variants.md): per-game DLL overrides without touching the shared runner.
- [`tools/rva.py`](tools/rva.py): reads values such as `D3D12SDKVersion` out of a Windows exe.

## Quick start: a DX12 game says "DirectX 12 not supported"

1. Read the per-game Wine log and find the **game's** process id (not the launcher's).
2. Check that process got `d3dmetal` as its backend (`WINEDEBUG=trace+cxcompatdb,trace+process`).
3. Check which `d3d12.dll` it loaded (`+loaddll`) and compare it with the stock GPTK file.
4. Fix per game with a runner variant, never by editing the shared runner.

Details in the [playbook](docs/troubleshooting-playbook.md).
