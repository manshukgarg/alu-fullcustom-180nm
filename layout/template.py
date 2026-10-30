"""Standard-cell template for the custom library (lambda units, 1 lambda = 0.1 um).

Row height 80 lambda (8.0 um). The ground rail is centred on y = 0 and the
supply rail on y = H, each 6 lambda wide, so rows abut and share rails when
alternate rows are mirrored. NMOS devices sit on the ground side, PMOS devices
on the supply side inside an n-well that starts at NW_Y0 and spans the full
cell width plus 6 lambda on each side (neighbouring wells merge).

Vertical budget:
    psc tap  -2..2   ndiff  6..30 (Wn <= 24)   gap 30..42   pdiff 42..74 (Wp <= 32)
    nsc tap  78..82  n-well 36..85
"""

H = 80              # cell height (rail centre to rail centre)
RAIL = 3            # half rail width: rails are y in [-3, 3] and [H-3, H+3]
YN0 = 6             # bottom edge of every NMOS diffusion
YP1 = 74            # top edge of every PMOS diffusion
NW_Y0 = 36          # n-well bottom edge
NW_Y1 = 85          # n-well top edge
WN_MAX = 24
WP_MAX = 32
EDGE = 2            # diffusion / metal1 inset from the left and right cell edges


def rails(L, width):
    """Ground and supply rails across the cell, with substrate and well taps."""
    L.paint("m1", 0, -RAIL, width, RAIL)
    L.paint("m1", 0, H - RAIL, width, H + RAIL)
    L.paint("nwell", -6, NW_Y0, width + 6, NW_Y1)


def taps(L, xs):
    """Substrate (psc) and well (nsc) contacts under the rails at the given x."""
    for x in xs:
        L.paint("psc", x, -2, x + 4, 2)
        L.paint("nsc", x, H - 2, x + 4, H + 2)


def ports_power(L, width):
    L.label("m1", 0, H - RAIL, EDGE, H + RAIL, "vdd", "power", "bidirectional")
    L.label("m1", 0, -RAIL, EDGE, RAIL, "gnd", "ground", "bidirectional")
