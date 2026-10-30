* Inverter transient characterization
* Input edge shaped by a driver inverter, fan-out-of-four load, 500 MHz input.
* The device under test has its own supply (Vdut) so its energy is measured alone.
.include ../models/tsmc018_t14b.lib
.include out/dut.spice

Vdd  vdd   0 1.8
Vdut vddut 0 1.8
Vin  in    0 PULSE(0 1.8 0.5n 50p 50p 0.95n 2n)

Xdrv in a vdd   0 inv
Xdut a  y vddut 0 inv
Xl1  y o1 vdd 0 inv
Xl2  y o2 vdd 0 inv
Xl3  y o3 vdd 0 inv
Xl4  y o4 vdd 0 inv

.tran 1p 6.5n

* second cycle is measured, so the start-up transient is excluded
.meas tran tphl trig v(a) val=0.9 rise=2 targ v(y) val=0.9 fall=2
.meas tran tplh trig v(a) val=0.9 fall=2 targ v(y) val=0.9 rise=2
.meas tran tf   trig v(y) val=1.62 fall=2 targ v(y) val=0.18 fall=2
.meas tran tr   trig v(y) val=0.18 rise=2 targ v(y) val=1.62 rise=2
.meas tran tp   param='(tphl+tplh)/2'
* energy drawn by the device under test over one 2 ns period (one rise, one fall)
.meas tran qdut integ i(Vdut) from=2.2n to=4.2n
.meas tran pavg param='-qdut*1.8/2e-9'
.meas tran pdp  param='pavg*tp'
.end
