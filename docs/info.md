<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project implements an **8-bit programmable binary counter** with:
1. **Asynchronous Reset (`rst_n`)**: Active-low reset that immediately sets the counter register to `8'h00`, independent of the clock.
2. **Synchronous Load (`load` on `uio_in[0]`)**: Active-high load enable. On the rising edge of `clk`, if `load` is high, the 8-bit value on `ui_in[7:0]` is loaded into the counter register.
3. **Binary Up-Counter**: When `rst_n` is high and `load` is low, the counter increments by 1 on each rising edge of `clk` (`count <= count + 1`).
4. **Tri-State Outputs (`oe` on `uio_in[1]`)**:
   - When `oe == 1`, the counter value is actively driven to `uo_out[7:0]` and `uio_out[7:0]` with `uio_oe[7:0] == 8'hFF`.
   - When `oe == 0`, `uo_out[7:0]` enters high-impedance (`8'bzzzz_zzzz`) and bidirectional output enables `uio_oe[7:0]` are de-asserted (`8'h00`).

## Pinout

| Pin | Direction | Function |
| --- | --- | --- |
| `clk` | Input | System Clock |
| `rst_n` | Input | Asynchronous Reset (active low) |
| `ena` | Input | Chip Enable (always 1) |
| `ui_in[7:0]` | Input | 8-bit Parallel Load Data (`d[7:0]`) |
| `uio_in[0]` | Input | Synchronous Load Enable (`load`, active high) |
| `uio_in[1]` | Input | Output Enable (`oe`, active high) |
| `uo_out[7:0]` | Output | 8-bit Counter Output (tri-state, high-Z when `oe=0`) |
| `uio_out[7:0]` | Output | 8-bit Counter Output (active when `oe=1`) |
| `uio_oe[7:0]` | Output | Output Enable controls (`8'hFF` when `oe=1`, `8'h00` when `oe=0`) |

## How to test

1. Apply `rst_n = 0` to asynchronously reset the counter; verify outputs clear to `8'h00`.
2. Release reset (`rst_n = 1`) with `oe = 1` and `load = 0`. Clock the design and verify the counter increments every rising edge (`0, 1, 2, ...`).
3. Set `load = 1` and apply a test pattern on `ui_in[7:0]` (e.g. `8'hA5`). After one rising clock edge, verify the counter outputs `8'hA5`.
4. Deassert `load = 0` and verify the counter resumes incrementing from `8'hA5` (`8'hA6, 8'hA7, ...`).
5. Set `oe = 0` and verify the outputs enter the high-impedance (tri-state) condition.

## External hardware

None required. Standard Tiny Tapeout demo board or GPIO header.
