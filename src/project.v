/*
 * Copyright (c) 2024 Ben Delvecchio
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_bdelvecc (
    input  wire [7:0] ui_in,    // Dedicated inputs: 8-bit parallel load data
    output wire [7:0] uo_out,   // Dedicated outputs: 8-bit counter output (tri-state)
    input  wire [7:0] uio_in,   // IOs: Input path (uio_in[0]=load, uio_in[1]=oe)
    output wire [7:0] uio_out,  // IOs: Output path: 8-bit counter output
    output wire [7:0] uio_oe,   // IOs: Enable path: active high when oe is high
    input  wire       ena,      // always 1 when the design is powered
    input  wire       clk,      // clock
    input  wire       rst_n     // asynchronous reset - active low
);

  // Control signals
  wire load = uio_in[0];  // Synchronous load enable (active high)
  wire oe   = uio_in[1];  // Output enable (active high)

  // 8-bit counter register
  reg [7:0] count;

  // Asynchronous reset, synchronous load, binary count logic
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= 8'h00;
    end else if (load) begin
      count <= ui_in;
    end else begin
      count <= count + 8'd1;
    end
  end

  // Tri-state outputs:
  // 1. Behavioral tri-state on dedicated outputs
  assign uo_out  = oe ? count : 8'bzzzz_zzzz;

  // 2. Physical ASIC tri-state control on bidirectional IOs
  assign uio_out = count;
  assign uio_oe  = {8{oe}};

  // Tie off unused inputs to prevent compiler/linter warnings
  wire _unused = &{ena, uio_in[7:2], 1'b0};

endmodule
