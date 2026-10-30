// 8-bit ALU, behavioural description (input to the automated standard-cell flow).
//
//   s    operation   y              c (carry)      v (signed overflow)
//   000  ADD         a + b          carry out      yes
//   001  SUB         a - b          carry out (1 = no borrow)   yes
//   010  INC         a + 1          carry out      yes
//   011  DEC         a - 1          carry out (1 = no borrow)   yes
//   100  AND         a & b          0              0
//   101  OR          a | b          0              0
//   110  XOR         a ^ b          0              0
//   111  NOT         ~a             0              0
//   z = (y == 0), n = y[7] for every operation.
module alu8 (
    input  [7:0] a,
    input  [7:0] b,
    input  [2:0] s,
    output reg [7:0] y,
    output reg c,
    output reg v,
    output z,
    output n
);
    reg [8:0] t;
    always @* begin
        t = 9'd0;
        c = 1'b0;
        v = 1'b0;
        case (s)
            3'b000: begin
                t = {1'b0, a} + {1'b0, b};
                y = t[7:0]; c = t[8];
                v = (a[7] == b[7]) && (y[7] != a[7]);
            end
            3'b001: begin
                t = {1'b0, a} + {1'b0, ~b} + 9'd1;
                y = t[7:0]; c = t[8];
                v = (a[7] != b[7]) && (y[7] != a[7]);
            end
            3'b010: begin
                t = {1'b0, a} + 9'd1;
                y = t[7:0]; c = t[8];
                v = (a == 8'h7f);
            end
            3'b011: begin
                t = {1'b0, a} + 9'h0ff;
                y = t[7:0]; c = t[8];
                v = (a == 8'h80);
            end
            3'b100: y = a & b;
            3'b101: y = a | b;
            3'b110: y = a ^ b;
            default: y = ~a;
        endcase
    end
    assign z = (y == 8'd0);
    assign n = y[7];
endmodule
