* Inverter DC transfer characteristic: switching threshold VM (Vin = Vout)
.include ../models/tsmc018_t14b.lib
.include out/dut.spice

Vdd vdd 0 1.8
Vin a 0 0
X1 a y vdd 0 inv
* difference node: crosses zero where Vout = Vin
Bd d 0 V=v(y)-v(a)

.dc Vin 0 1.8 1m
.meas dc vm find v(a) when v(d)=0
.end
