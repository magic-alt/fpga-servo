# Agent rules

- Never read, display, log, or transmit sensitive environment-variable values or `.env` contents. Mention variable names only; redact any user-provided credentials before external use.
- Make hardware changes on a topic branch. Preserve existing uncommitted work; never reset or overwrite it to switch branches. The active OCP repair branch is `fix/ocp-latch-industrial-review`; verify the actual branch before edits.
- For this project's schematic/ERC/PCB work, read `.agents/skills/fpga-servo-kicad-repair/SKILL.md` and `docs/release_gates.md`.

## 电源与 GND 可见连线规则（强制）

- 电源、GND 和 PWR_FLAG 必须就近放在其服务的实际电路节点上，并通过原生导线连接到真实元件引脚。禁止把这些符号放在页边、空白区或独立图例中，仅用同名标签关联电路。
- 子页电源/GND 层次端口也必须沿可见导线接入实际电路；禁止孤立的“层次端口—电源符号”短线。局部去耦、上拉/下拉、滤波及供电回路必须能直接辨认其连接关系。
- 电源优先在上、GND 优先在下；使用 50 mil 正交连线和清晰分支点。禁止导线穿过无关引脚、符号或文字；不能为追求全页连续地线而制造长绕线。
- 跨功能块或跨页连接可以保留标签，但同名标签、靠近导线及零 ERC 都不能代替局部可见连接证明。现有被动电源图形不负责命名网络，不能为美观删除其必要的网络标签。
- 移动端口、符号或引线后，检查新端点是否碰到其他网络；新增 T 分支须正确分段并放置连接点。重新导出修改前后 KiCad XML 网表，要求元件身份、网名和每个物理引脚的归属精确一致；电气变更须另有明确授权。
- 原理图验收必须运行 `python tools/check_power_wiring.py`、项目全部检查和原生 ERC，并逐页查看导出图及电源/地密集区域。不得通过忽略检查、隐藏符号、删除连接或改为 NC 绕过验收。

# Repository Guidelines

## Project Structure & Module Organization

`hardware/` contains the Rev.A KiCad schematic hierarchy, PCB baseline, local symbol library, and BOM. `fpga/ax7010_servo_reva.xdc` defines AX7010 PL pin constraints. `docs/` holds architecture, interface, bring-up, calculations, and release-gate notes. `tools/` contains standalone Python checks; `.github/workflows/` runs them in CI. There is no firmware or HDL implementation in this repository yet.

## Build, Test, and Development Commands

Run the repository checks from the root with Python 3.12:

```sh
python tools/check_native_schematic.py
python tools/check_kicad_grid.py
python tools/check_schematic_layout.py
python tools/check_schematic_connectivity.py
python tools/check_power_wiring.py
python tools/check_design.py
```

These validate native schematic syntax, the connection grid, layout and connectivity rules, and required design files. For schematic changes, run KiCad ERC from `hardware/`:

```sh
kicad-cli sch erc --exit-code-violations --severity-all ax7010_servo_reva.kicad_sch
```

Open `hardware/ax7010_servo_reva.kicad_pcb` in KiCad for board review and DRC. The PCB remains a development baseline; consult `docs/release_gates.md` before treating outputs as fabrication ready.

## Coding Style & Naming Conventions

Use four-space indentation in Python and keep checks executable as standalone `tools/check_*.py` scripts. Follow the existing lower-case, underscore-separated file names. Use KiCad 10 native `.kicad_sch` and `.kicad_sym`: A4 landscape, valid hierarchical ports, and a 50 mil connection grid. Keep project-local symbols and embedded symbols consistent; resolve the library through `hardware/sym-lib-table`. Update the XDC and interface documentation together when pin assignments change.

## Testing Guidelines

The Python checks are the repository's regression tests; no separate test framework or coverage target is configured. Run all six checks above before a PR. For hardware edits, also run ERC and document any remaining violations; review PCB DRC where layout changes apply. Add a focused `check_*.py` rule when introducing a new machine-checkable design constraint.

## Commit & Pull Request Guidelines

Recent commits use Conventional Commit style, such as `fix(schematic): ...`, `test(kicad): ...`, and `ci(kicad): ...`. Keep each commit scoped to one change. In PRs, explain the affected schematic or board area, link the relevant issue when one exists, list checks run, and include ERC/DRC findings plus screenshots or exports for visual layout changes. Do not commit credentials or expose their values in logs or PR text.

## Native netlist and hardware acceptance

Export a fresh netlist before checking safety connectivity:

```sh
kicad-cli sch export netlist --output artifacts/ax7010_servo_reva.net hardware/ax7010_servo_reva.kicad_sch
python tools/check_netlist_safety.py artifacts/ax7010_servo_reva.net
python tools/check_ocp_behavior.py artifacts/ax7010_servo_reva.net
```

Do not reduce ERC/DRC severities, add blanket exclusions, delete connections, or mark required pins NC to get zero counts. Record fresh component/net counts and ERC errors/warnings/exclusions. Compare netlist references, physical pin numbers, footprints and nets before PCB synchronization. Preserve board snapshots and mechanical features; old baseline footprints may be placeholders.

Separate schematic correctness, placement readiness and fabrication readiness. Zero ERC does not validate OCP timing, regeneration energy, current/thermal ratings, vendor footprints or board routing. Layout freeze requires the release gates and fresh DRC with no unconnected items. Update BOM and interface documents with electrical changes; verify data sheets for package pin maps.
