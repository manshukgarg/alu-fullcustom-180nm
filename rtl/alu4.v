// 4-bit ALU, behavioural description (input to the automated standard-cell flow).
//
//   s    operation   y        c (carry)                    v (signed overflow)
//   000  ADD         a + b    carry out                    yes
//   001  SUB         a - b    carry out (1 = no borrow)    yes
//   010  INC         a + 1    carry out                    yes
//   011  DEC         a - 1    carry out (1 = no borrow)    yes
//   100  AND         a & b    0                            0
//   101  OR          a | b    0                            0
//   110  XOR         a ^ b    0                            0
//   111  NOT         ~a       0                            0
//   z = (y == 0) and n = y[W-1] for every operation.
// W = 4 is the project ALU; the description is valid for any W >= 2.
module alu4 #(parameter W = 4) (
    input      [W-1:0] a,
    input      [W-1:0] b,
    input      [2:0]   s,
    output reg [W-1:0] y,
    output reg         c,
    output reg         v,
    output             z,
    output             n
);
    localparam [W-1:0] MAXP = {1'b0, {(W-1){1'b1}}};   // largest positive value
    localparam [W-1:0] MINN = {1'b1, {(W-1){1'b0}}};   // most negative value

    reg [W:0] t;
    always @* begin
        t = {(W+1){1'b0}};
        y = {W{1'b0}};
        c = 1'b0;
        v = 1'b0;
        case (s)
            3'b000: begin
                t = {1'b0, a} + {1'b0, b};
                y = t[W-1:0]; c = t[W];
                v = (a[W-1] == b[W-1]) && (y[W-1] != a[W-1]);
            end
            3'b001: begin
                t = {1'b0, a} + {1'b0, ~b} + 1'b1;
                y = t[W-1:0]; c = t[W];
                v = (a[W-1] != b[W-1]) && (y[W-1] != a[W-1]);
            end
            3'b010: begin
                t = {1'b0, a} + 1'b1;
                y = t[W-1:0]; c = t[W];
                v = (a == MAXP);
            end
            3'b011: begin
                t = {1'b0, a} + {1'b0, {W{1'b1}}};
                y = t[W-1:0]; c = t[W];
                v = (a == MINN);
            end
            3'b100: y = a & b;
            3'b101: y = a | b;
            3'b110: y = a ^ b;
            default: y = ~a;
        endcase
    end
    assign z = (y == {W{1'b0}});
    assign n = y[W-1];
endmodule
