# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer


async def start_clock_and_reset(dut):
    """Start clock and perform initial power-up reset."""
    clock = Clock(dut.clk, 20, unit="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0b00000010  # load=0, oe=1
    dut.rst_n.value = 0            # active-low reset asserted

    # Hold reset across 2 clock cycles
    await ClockCycles(dut.clk, 2)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1            # release reset on falling edge
    await FallingEdge(dut.clk)     # wait for next cycle to settle


@cocotb.test()
async def test_counter_counting(dut):
    """Test sequential binary up-counting."""
    dut._log.info("--- Test 1: Sequential Binary Up-Counting ---")
    await start_clock_and_reset(dut)

    # Reset synchronously to start at 0
    dut.rst_n.value = 0
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)

    # After reset release, counter starts incrementing on each rising edge
    # We sample on FallingEdge to allow full propagation
    start_val = dut.uo_out.value.to_unsigned()
    dut._log.info(f"Initial count after reset: {start_val}")

    for i in range(1, 20):
        await FallingEdge(dut.clk)
        current = dut.uo_out.value.to_unsigned()
        expected = (start_val + i) & 0xFF
        assert current == expected, f"Cycle {i}: expected {expected}, got {current}"
        assert dut.uio_out.value.to_unsigned() == expected
        assert dut.uio_oe.value.to_unsigned() == 0xFF


@cocotb.test()
async def test_synchronous_load(dut):
    """Test parallel synchronous load on clock edge."""
    dut._log.info("--- Test 2: Synchronous Load ---")
    await start_clock_and_reset(dut)

    # Drive load=1 and test value on falling edge (providing setup time before rising edge)
    test_pattern = 0xA5
    dut.ui_in.value = test_pattern
    dut.uio_in.value = 0b00000011  # load=1, oe=1
    await FallingEdge(dut.clk)

    # Verify that the value was loaded on the rising edge
    loaded_val = dut.uo_out.value.to_unsigned()
    assert loaded_val == test_pattern, (
        f"Synchronous load failed: expected {hex(test_pattern)}, got {hex(loaded_val)}"
    )

    # De-assert load (load=0, oe=1) on falling edge
    dut.uio_in.value = 0b00000010
    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() == (test_pattern + 1) & 0xFF

    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() == (test_pattern + 2) & 0xFF

    # Load another pattern: 0x3C
    dut.ui_in.value = 0x3C
    dut.uio_in.value = 0b00000011
    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() == 0x3C


@cocotb.test()
async def test_counter_overflow(dut):
    """Test 8-bit counter overflow wrapping from 0xFF to 0x00."""
    dut._log.info("--- Test 3: 8-bit Overflow Wrap-Around ---")
    await start_clock_and_reset(dut)

    # Load 0xFE
    dut.ui_in.value = 0xFE
    dut.uio_in.value = 0b00000011  # load=1, oe=1
    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() == 0xFE

    # Turn off load, count to 0xFF
    dut.uio_in.value = 0b00000010  # load=0, oe=1
    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() == 0xFF

    # Wrap around to 0x00
    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() == 0x00

    # Continue to 0x01
    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() == 0x01


@cocotb.test()
async def test_asynchronous_reset(dut):
    """Test that rst_n=0 resets counter asynchronously without waiting for clock."""
    dut._log.info("--- Test 4: Asynchronous Reset Verification ---")
    await start_clock_and_reset(dut)

    # Load a known non-zero value: 0x88
    dut.ui_in.value = 0x88
    dut.uio_in.value = 0b00000011
    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() == 0x88

    # Switch to counting mode for a couple cycles
    dut.uio_in.value = 0b00000010
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() > 0

    # Assert reset asynchronously mid-cycle (at falling edge where no rising edge occurs)
    dut.rst_n.value = 0
    # Wait a brief propagation delay (2 ns) without any clock transition
    await Timer(2, unit="ns")

    # Output must immediately clear to 0
    assert dut.uo_out.value.to_unsigned() == 0, (
        f"Async reset failed: expected 0, got {dut.uo_out.value.to_unsigned()}"
    )

    # Release reset and ensure normal operation resumes
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() == 1


@cocotb.test()
async def test_tristate_output_enable(dut):
    """Test tri-state output control via oe signal."""
    dut._log.info("--- Test 5: Tri-State Output Enable ---")
    await start_clock_and_reset(dut)

    # Load 0x77 with oe=1
    dut.ui_in.value = 0x77
    dut.uio_in.value = 0b00000011  # load=1, oe=1
    await FallingEdge(dut.clk)
    assert dut.uo_out.value.to_unsigned() == 0x77
    assert dut.uio_out.value.to_unsigned() == 0x77
    assert dut.uio_oe.value.to_unsigned() == 0xFF

    # De-assert output enable (oe=0, load=0)
    dut.uio_in.value = 0b00000000
    await Timer(2, unit="ns")

    # Hardware tri-state check on bidirectional IOs (active in both RTL & Gate-Level)
    assert dut.uio_oe.value.to_unsigned() == 0x00, "Expected uio_oe == 0 when oe=0"

    # In RTL simulation, uo_out enters high-impedance ('z').
    # In Gate-Level (GL) simulation, physical standard cells drive push-pull CMOS levels on uo_out.
    is_gl = (hasattr(dut, "is_gl_test") and dut.is_gl_test.value == 1) or hasattr(dut, "VPWR")
    val_str = str(dut.uo_out.value).lower()
    dut._log.info(f"uo_out with oe=0: {val_str} (is_gl_test={is_gl})")
    if not is_gl:
        assert 'z' in val_str, f"Expected high-impedance 'z' in RTL simulation, got {val_str}"

    # Re-enable output (oe=1)
    dut.uio_in.value = 0b00000010
    await Timer(2, unit="ns")
    if not is_gl:
        assert 'z' not in str(dut.uo_out.value).lower()
    assert dut.uio_oe.value.to_unsigned() == 0xFF
    assert dut.uo_out.value.to_unsigned() == 0x77
