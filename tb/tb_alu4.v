// Exhaustive self-checking testbench of the 4-bit ALU: 8 operations x 16 x 16 operands.
// Expected results are computed with integer arithmetic (unsigned for y and c,
// signed for v), independently of the bit-level formulation of the design.
// Define GATE when simulating a gate-level netlist with cell delays.
`timescale 1ns/10ps
module tb_alu4;
    localparam W = 4;
    localparam N = 8 << (2 * W);
    localparam integer MAXS = (1 << (W - 1)) - 1;    // signed range of a W-bit operand
    localparam integer MINS = -(1 << (W - 1));

    reg  [W-1:0] a, b;
    reg  [2:0]   s;
    wire [W-1:0] y;
    wire c, v, z, n;

    alu4 dut (.a(a), .b(b), .s(s), .y(y), .c(c), .v(v), .z(z), .n(n));

    integer i, ia, ib, sa, sb, r, sr, errors, shown;
    reg [31:0]  rr;
    reg [W-1:0] ey;
    reg ec, ev, arith;

    initial begin
        errors = 0;
        shown = 0;
        for (i = 0; i < N; i = i + 1) begin
            {s, a, b} = i;
`ifdef GATE
            #10;
`else
            #1;
`endif
            ia = a;
            ib = b;
            sa = a[W-1] ? ia - (1 << W) : ia;
            sb = b[W-1] ? ib - (1 << W) : ib;
            arith = 1'b1;
            ec = 1'b0;
            sr = 0;
            case (s)
                3'd0: begin r = ia + ib; sr = sa + sb; ec = (r >= (1 << W)); end
                3'd1: begin r = ia - ib; sr = sa - sb; ec = (ia >= ib);      end
                3'd2: begin r = ia + 1;  sr = sa + 1;  ec = (r >= (1 << W)); end
                3'd3: begin r = ia - 1;  sr = sa - 1;  ec = (ia >= 1);       end
                3'd4: begin r = ia & ib; arith = 1'b0; end
                3'd5: begin r = ia | ib; arith = 1'b0; end
                3'd6: begin r = ia ^ ib; arith = 1'b0; end
                default: begin r = ~ia;  arith = 1'b0; end
            endcase
            rr = r;
            ey = rr[W-1:0];
            ev = arith && (sr > MAXS || sr < MINS);
            if ({y, c, v, z, n} !== {ey, ec, ev, (ey == {W{1'b0}}), ey[W-1]}) begin
                errors = errors + 1;
                if (shown < 10) begin
                    shown = shown + 1;
                    $display("MISMATCH s=%b a=%h b=%h : y=%h c=%b v=%b z=%b n=%b  expected y=%h c=%b v=%b z=%b n=%b",
                             s, a, b, y, c, v, z, n, ey, ec, ev, (ey == {W{1'b0}}), ey[W-1]);
                end
            end
        end
        $display("TESTS %0d ERRORS %0d", N, errors);
        $finish;
    end
endmodule
