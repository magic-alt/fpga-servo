"""TI TXU0204PW (SCES936A Table6-1) voltage and partial-power isolation."""


def symbol(prop,effects,at):
    pins=[(1,"VCCA","power_in",-7.62,30.48,270),(14,"VCCB","power_in",7.62,30.48,270),
          (2,"A1","input",-22.86,12.7,0),(3,"A2","input",-22.86,5.08,0),
          (4,"A3Y","output",-22.86,-10.16,0),(5,"A4Y","output",-22.86,-17.78,0),
          (13,"B1Y","output",22.86,12.7,180),(12,"B2Y","output",22.86,5.08,180),
          (11,"B3","input",22.86,-10.16,180),(10,"B4","input",22.86,-17.78,180),
          (8,"OE","input",-22.86,-30.48,0),(7,"GND","power_in",0,-43.18,90),
          (6,"NC","no_connect",-7.62,-43.18,90),(9,"NC","no_connect",7.62,-43.18,90)]
    result='(symbol "TXU0204PW" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)'
    result+=prop("Reference","U")+prop("Value","TXU0204PW")
    result+='(symbol "TXU0204PW_0_1" (rectangle (start -15.24 22.86) (end 15.24 -35.56) (stroke (width .254) (type default)) (fill (type background))))'
    result+='(symbol "TXU0204PW_1_1"'
    for number,name,kind,x,y,angle in pins:
        result+=f'(pin {kind} line {at(x,y,angle)} (length 7.62) (name "{name}" {effects(.85)}) (number "{number}" {effects(.85)}))'
    return result+'))'


def records(b):
    sheet="adc_levelshift"
    r=[b.text("ADC POWER-DOMAIN ISOLATION: FPGA 3.3 V <-> ADC VA_5V",17.78,15.24),
       b.text("U6 AVCC = VDRIVE = VA_5V; never connect AX7010 3.3 V directly to U6.23",17.78,20.32,1.016)]
    routes=[
        ("U27",63.5,["CONVST","RESET"],["DOUTA","DOUTB"]),
        ("U28",154.94,["SCLK","CS_N"],["DOUTC","DOUTD"]),
        ("U29",246.38,["SDI",None],["BUSY","FRSTDATA"])]
    for i,(ref,x,forward,reverse) in enumerate(routes):
        r += [b.component("TXU0204PW",ref,"TXU0204PWR",x,86.36,sheet,metadata={
            "Manufacturer":"Texas Instruments","MPN":"TXU0204PWR","LCSC":"UNVERIFIED",
            "Footprint":"Package_SO:TSSOP-14_4.4x5mm_P0.65mm",
            "Datasheet":"https://www.ti.com/lit/ds/symlink/txu0204.pdf",
            "Description":"2 forward + 2 reverse fixed channels; Ioff and VCC disconnect isolation",
            "Sourcing_Status":"OEM pin/package reviewed; quote and procurement not verified"})]
        # Two dedicated bypass capacitors and short visible supply branches.
        for side,net in [(-1,"VIO_3V3"),(1,"VA_5V")]:
            px=round(x+side*7.62,6);cx=round(x+side*17.78,6)
            r += [b.wire((px,27.94),(px,55.88)),b.wire((min(px,cx),27.94),(max(px,cx),27.94)),
                  b.wire((cx,27.94),(cx,36.83)),b.passive("C43",f"C{101+i*2+(side==1)}",cx,43.18,sheet,"100nF local TXU0204 supply bypass"),
                  b.wire((cx,49.53),(cx,53.34)),b.power("GND",cx,53.34,sheet),b.label("GND",cx,53.34),
                  b.power(net,px,27.94,sheet),b.label(net,px,27.94)]
            if i==0:
                hx=30.48 if side<0 else 99.06
                r += [b.wire((min(hx,cx),27.94),(max(hx,cx),27.94)),
                      b.label(net,hx,27.94,True,angle=0 if side<0 else 180),b.junction(cx,27.94)]
        for j,name in enumerate(forward):
            y=73.66+j*7.62;left=round(x-22.86,6);right=round(x+22.86,6)
            if name:
                hx=round(x-48.26,6);rx=round(x+33.02,6)
                r += [b.wire((hx,y),(left,y)),b.label("ADC_"+name,hx,y,True),
                      b.wire((right,y),(rx,y)),b.label("ADC5_"+name,rx,y,True,"output",180)]
            else:
                # Spare A->B channel: input held low, output genuinely unused.
                r += [b.wire((left-5.08,y),(left,y)),b.wire((left-5.08,y),(left-5.08,y+5.08)),
                      b.power("GND",left-5.08,y+5.08,sheet),b.label("GND",left-5.08,y+5.08),b.no_connect(right,y)]
        for j,name in enumerate(reverse):
            y=96.52+j*7.62;left=round(x-22.86,6);right=round(x+22.86,6)
            hx=round(x-48.26,6);rx=round(x+33.02,6)
            if i<2:
                cx=round(x-35.56,6)
                hy=round(y+(-5.08 if j==0 else 5.08),6)
                rp=round(cx-7.62,6)
                r += [b.wire((left-5.08,y),(left,y)),b.passive("R40",f"R{100+i*2+j}",cx,y,sheet,"47R J10 DOUT source damping; place next to translator A output"),
                      b.wire((hx,hy),(rp,hy)),b.wire((rp,hy),(rp,y)),b.label("ADC_"+name,hx,hy,True,"output")]
            else:
                r += [b.wire((hx,y),(left,y)),b.label("ADC_"+name,hx,y,True,"output")]
            r += [b.wire((right,y),(rx,y)),b.label("ADC5_"+name,rx,y,True,angle=180)]
        left=round(x-22.86,6);hx=round(x-48.26,6)
        r += [b.wire((hx,116.84),(left,116.84)),b.label("PWR_READY",hx,116.84,hierarchy=i==0),
              b.no_connect(round(x-7.62,6),129.54),b.no_connect(round(x+7.62,6),129.54),
              b.wire((x,129.54),(x,137.16)),b.power("GND",x,137.16,sheet),b.label("GND",x,137.16)]
        if i==0:
            r += [b.wire((15.24,137.16),(x,137.16)),b.label("GND",15.24,137.16,True),b.junction(x,137.16)]
    r += [b.text("OE follows PWR_READY: translators disable on supervised rail faults.",17.78,149.86,1.016),
          b.text("TI Ioff / VCC disconnect prevents back-power when either supply is off.",17.78,156.21,1.016),
          b.text("RESET / CS pulls are on the ADC side. Firmware must apply full RESET after OE is enabled.",17.78,162.56,1.016),
          b.text("Translate delay, J10 flight time and ADC delay must all be included in Vivado I/O timing.",17.78,170.18,.9)]
    return r
