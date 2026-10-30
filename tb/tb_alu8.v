// Exhaustive self-checking testbench: all 8 operations x 256 x 256 operands.
// The expected results are computed here, independently of the design.
// Define GATE when simulating a gate-level netlist with cell delays.
`timescale 1ns/10ps
module tb_alu8;
    reg  [7:0] a, b;
    reg  [2:0] s;
    wire [7:0] y;
    wire c, v, z, n;

    alu8 dut (.a(a), .b(b), .s(s), .y(y), .c(c), .v(v), .z(z), .n(n));

    reg  [8:0] t;
    reg  [7:0] ey;
    reg  ec, ev;
    integer i, errors, shown;

    initial begin
        errors = 0;
        shown = 0;
        for (i = 0; i < 8 * 256 * 256; i = i + 1) begin
            {s, a, b} = i;
`ifdef GATE
            #10;
`else
            #1;
`endif
            ec = 1'b0;
            ev = 1'b0;
            case (s)
                3'd0: begin t = a + b;         ec = t[8]; ey = t[7:0];
                            ev = (a[7] == b[7]) && (ey[7] != a[7]); end
                3'd1: begin t = a + (~b & 8'hff) + 1; ec = t[8]; ey = t[7:0];
                            ev = (a[7] != b[7]) && (ey[7] != a[7]); end
                3'd2: begin t = a + 1;         ec = t[8]; ey = t[7:0]; ev = (a == 8'h7f); end
                3'd3: begin t = a + 8'hff;     ec = t[8]; ey = t[7:0]; ev = (a == 8'h80); end
                3'd4: ey = a & b;
                3'd5: ey = a | b;
                3'd6: ey = a ^ b;
                default: ey = ~a;
            endcase
            if ({y, c, v, z, n} !== {ey, ec, ev, (ey == 8'd0), ey[7]}) begin
                errors = errors + 1;
                if (shown < 10) begin
                    shown = shown + 1;
                    $display("MISMATCH s=%b a=%h b=%h : y=%h c=%b v=%b z=%b n=%b  expected y=%h c=%b v=%b z=%b n=%b",
                             s, a, b, y, c, v, z, n, ey, ec, ev, (ey == 8'd0), ey[7]);
                end
            end
        end
        $display("TESTS %0d ERRORS %0d", 8 * 256 * 256, errors);
        $finish;
    end
endmodule
