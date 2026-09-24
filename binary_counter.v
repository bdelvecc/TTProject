/*
 * 8-Bit Programmable Binary Counter for 8bitworkshop
 * ECE-298A Project
 *
 * Features:
 *   - 8-bit binary counter
 *   - Asynchronous reset (rst_n)
 *   - Synchronous parallel load (load)
 *   - Tri-state outputs (oe)
 *
 * When pasted into https://8bitworkshop.com/v3.9.0/?platform=verilog&file=binary_counter.v
 * the `top` module automatically provides clock and stimulus so you can inspect
 * all counter features in the 8bitworkshop Logic Analyzer / Scope view!
 */

`default_nettype none

// ============================================================================
// Top-level module for 8bitworkshop simulation and waveform viewer
// ============================================================================
module top (
    input  wire       clk,        // Clock provided by 8bitworkshop
    input  wire       reset,      // Reset provided by 8bitworkshop (active high)
    output wire [7:0] counter_out,// Tri-state counter output
    output wire       load_signal,// Synchronous load control
    output wire       oe_signal,  // Output enable control (tri-state)
    output wire [7:0] load_data,  // Parallel data bus to load
    output wire       async_rst_n // Active-low asynchronous reset
);

  // 6-bit step sequencer to generate test stimulus automatically
  reg [5:0] seq = 6'd0;

  always @(posedge clk or posedge reset) begin
    if (reset) begin
      seq <= 6'd0;
    end else begin
      seq <= seq + 6'd1;
    end
  end

  // Stimulus generation:
  // 1. Asynchronous Reset: active low when seq is between 0 and 2
  assign async_rst_n = (seq >= 6'd3);

  // 2. Synchronous Load: pulse high at seq=16 and seq=36
  assign load_signal = (seq == 6'd16) || (seq == 6'd36);

  // 3. Parallel Load Data:
  //    At seq=16, load 8'hA5 (165)
  //    At seq=36, load 8'hFE (254) to demonstrate overflow wrap-around
  assign load_data = (seq == 6'd36) ? 8'hFE : 8'hA5;

  // 4. Output Enable (Tri-State):
  //    Disable (high-Z) during seq 26..29 to show tri-state behavior
  assign oe_signal = !(seq >= 6'd26 && seq <= 6'd29);

  // Instantiate the 8-bit programmable counter
  programmable_counter_8bit dut (
      .clk      (clk),
      .rst_n    (async_rst_n),
      .load     (load_signal),
      .data_in  (load_data),
      .oe       (oe_signal),
      .count_out(counter_out)
  );

endmodule


// ============================================================================
// Core Module: 8-Bit Programmable Binary Counter
// ============================================================================
module programmable_counter_8bit (
    input  wire       clk,        // Clock
    input  wire       rst_n,      // Asynchronous reset (active low)
    input  wire       load,       // Synchronous load enable (active high)
    input  wire [7:0] data_in,    // 8-bit parallel load input
    input  wire       oe,         // Output enable (active high)
    output wire [7:0] count_out   // 8-bit tri-state output
);

  reg [7:0] count;

  // Asynchronous reset and synchronous load logic
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= 8'h00;
    end else if (load) begin
      count <= data_in;
    end else begin
      count <= count + 8'd1;
    end
  end

  // Tri-state buffer: when oe=0, output floats to high-impedance ('z')
  assign count_out = oe ? count : 8'bzzzz_zzzz;

endmodule
