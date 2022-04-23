from typing import Counter
from amaranth import *
from amaranth.build import Platform
from colorlight_i5_r7_0_ext_board import *
from amaranth.back import verilog


class Hdmi(Elaboratable):
    def __init__(self,
                i_reset, 
                i_red,
                i_grn,
                i_blu,
                o_rd,
                o_newline,
                o_newframe,
                o_red,
                o_grn,
                o_blu):

        
        self.i_reset = i_reset 
        self.i_red = i_red
        self.i_grn = i_grn
        self.i_blu = i_blu
        self.o_rd  = o_rd
        self.o_newline = o_newline
        self.o_newframe = o_newframe
        self.o_red = o_red
        self.o_grn = o_grn
        self.o_blu = o_blu


    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        self.CounterX = Signal(10)
        self.CounterY = Signal(10)
        self.hSync = Signal()
        self.vSync = Signal()
        self.drawArea = Signal()


        with m.If (self.i_reset == 1):
            m.d.clk_25MHz += self.CounterX.eq(0)
        with m.Else():
            with m.If(self.CounterX == 799 ):
                m.d.clk_25MHz += self.CounterX.eq( 0 )
            with m.Else():
                m.d.clk_25MHz += self.CounterX.eq( self.CounterX + 1)

        with m.If (self.i_reset == 1):
            m.d.clk_25MHz += self.CounterY.eq(0)
        with m.Elif (self.CounterX == 799):
            with m.If(self.CounterY == 524 ):
                m.d.clk_25MHz += self.CounterY.eq( 0 )
            with m.Else():
                m.d.clk_25MHz += self.CounterY.eq( self.CounterY + 1)

        with m.If (self.CounterX == 639):
            m.d.clk_25MHz += self.o_newline.eq(1)
            with m.If (self.CounterY == 479):
                m.d.clk_25MHz += self.o_newframe.eq(1)
            with m.Else ():
                m.d.clk_25MHz += self.o_newframe.eq(0)
        with m.Else():
            m.d.clk_25MHz += self.o_newline.eq(0)

        with m.If ((self.CounterX<640) & (self.CounterY<480)):
            m.d.clk_25MHz += self.drawArea.eq(1)
        with m.Else():
            m.d.clk_25MHz += self.drawArea.eq(0)

        m.d.clk_25MHz += self.o_rd.eq(self.drawArea & ~self.i_reset)

        with m.If((self.CounterX >= 656) & (self.CounterX<752)):
            m.d.clk_25MHz += self.hSync.eq(1)
        with m.Else():
            m.d.clk_25MHz += self.hSync.eq(0)

        with m.If((self.CounterY >= 490) & (self.CounterY<492)):
            m.d.clk_25MHz += self.vSync.eq(1)
        with m.Else():
            m.d.clk_25MHz += self.vSync.eq(0)

        self.TMDS_red = Signal(10)
        self.TMDS_grn = Signal(10)
        self.TMDS_blu = Signal(10)


        encoder_R = TMDS_encoder(
            VD = self.i_red,
            CD = Signal(2),
            VDE = self.drawArea,
            TMDS = self.TMDS_red,
        )
        encoder_G = TMDS_encoder(
            VD = self.i_grn,
            CD = Signal(2),
            VDE = self.drawArea,
            TMDS = self.TMDS_grn,
        )
        encoder_B = TMDS_encoder(
            VD = self.i_blu,
            CD = Cat(self.vSync, self.hSync),
            VDE = self.drawArea,
            TMDS = self.TMDS_blu,
        )
        m.submodules += encoder_R
        m.submodules += encoder_G
        m.submodules += encoder_B

        self.TMDS_mod10=Signal(4)
        self.TMDS_shift_load=Signal()

        with m.If (self.i_reset == 1):
            m.d.sync += self.TMDS_mod10.eq(0)
            m.d.sync += self.TMDS_shift_load.eq(0)
        with m.Else():
            with m.If(self.TMDS_mod10 == 9 ):
                m.d.sync += self.TMDS_mod10.eq( 0 )
                m.d.sync += self.TMDS_shift_load.eq(1)
            with m.Else():
                m.d.sync += self.TMDS_mod10.eq( self.TMDS_mod10 + 1)
                m.d.sync += self.TMDS_shift_load.eq(0)
            
        self.TMDS_shift_red = Signal(10)
        self.TMDS_shift_grn = Signal(10)
        self.TMDS_shift_blu = Signal(10)

        with m.If (self.i_reset == 1):
            m.d.sync += self.TMDS_shift_red.eq(0)
            m.d.sync += self.TMDS_shift_grn.eq(0)
            m.d.sync += self.TMDS_shift_blu.eq(0)
        with m.Else():
            with m.If(self.TMDS_shift_load == 1 ):
                m.d.sync += self.TMDS_shift_red.eq(self.TMDS_red )
                m.d.sync += self.TMDS_shift_grn.eq(self.TMDS_grn )
                m.d.sync += self.TMDS_shift_blu.eq(self.TMDS_blu )
            with m.Else():
                m.d.sync += self.TMDS_shift_red.eq(Cat(Const(0),self.TMDS_shift_red[1:10]))
                m.d.sync += self.TMDS_shift_grn.eq(Cat(Const(0),self.TMDS_shift_grn[1:10]))
                m.d.sync += self.TMDS_shift_blu.eq(Cat(Const(0),self.TMDS_shift_blu[1:10]) )

        m.d.comb += self.o_red.eq(self.TMDS_shift_red[0])
        m.d.comb += self.o_grn.eq(self.TMDS_shift_grn[0])
        m.d.comb += self.o_blu.eq(self.TMDS_shift_blu[0])

        return m


class TMDS_encoder(Elaboratable):
    def __init__(self, VD, CD, VDE, TMDS):
        self.VD = VD
        self.CD = CD
        self.VDE = VDE
        self.TMDS = TMDS

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        N1s = Signal(4)
        #remove cat
        
        m.d.comb += N1s.eq(self.VD[0] + self.VD[1]
                + self.VD[2] + self.VD[3]
                + self.VD[4] + self.VD[5]
                + self.VD[6] + self.VD[7])

        XNOR = Signal()
        with m.If (N1s > 4 | ((N1s==4) & (self.VD[0] == 0))):
            m.d.comb += XNOR.eq(1)
        with m.Else():
            m.d.comb += XNOR.eq(0)
        
        QM0, QM1, QM2, QM3, QM4, QM5, QM6, QM7, QM8 = Signal(), Signal(), Signal(), Signal() , Signal(), Signal(), Signal(),Signal(), Signal() 
         
        m.d.comb += QM0.eq(self.VD[0])
        m.d.comb += QM1.eq(QM0 ^ self.VD[1] ^ XNOR)
        m.d.comb += QM2.eq(QM1 ^ self.VD[2] ^ XNOR)
        m.d.comb += QM3.eq(QM2 ^ self.VD[3] ^ XNOR)
        m.d.comb += QM4.eq(QM3 ^ self.VD[4] ^ XNOR)
        m.d.comb += QM5.eq(QM4 ^ self.VD[5] ^ XNOR)
        m.d.comb += QM6.eq(QM5 ^ self.VD[6] ^ XNOR)
        m.d.comb += QM7.eq(QM6 ^ self.VD[7] ^ XNOR)
        m.d.comb += QM8.eq(~XNOR)

        q_m = Signal(9)
        m.d.comb += q_m.eq(Cat(QM0, QM1, QM2, QM3, QM4, QM5, QM6, QM7, QM8))

        balance_acc = Signal(4)
        balance = Signal(4)
        m.d.comb += balance.eq(q_m[0]
                + q_m[1]+ q_m[2] + q_m[3] + q_m[4] 
                + q_m[5] + q_m[6] + q_m[7] - Const(4, unsigned(4)))

        balance_sign_eq = Signal()
        m.d.comb += balance_sign_eq.eq(balance[3] == balance_acc[3])

        invert_q_m = Signal()
        with m.If((balance == 0) | (balance_acc==0)):
            m.d.comb += invert_q_m.eq(~q_m[8])
        with m.Else():
            m.d.comb += invert_q_m.eq(balance_sign_eq)

        
        balance_acc_inc = Signal(4)
        m.d.comb += balance_acc_inc.eq(balance 
                - Cat(((q_m[8] ^ ~balance_sign_eq) 
                    & ~( (balance==0) | (balance_acc==0)))
                    , Const(0,unsigned(3))))
        balance_acc_new = Signal(4)
        with m.If(invert_q_m == 1):
            m.d.comb += balance_acc_new.eq(balance_acc-balance_acc_inc)
        with m.Else():
            m.d.comb += balance_acc_new.eq(balance_acc+balance_acc_inc)


        TMDS_data = Signal(10)
        TMDS_code = Signal(10)
        m.d.comb += TMDS_data.eq(Cat(q_m[:8] ^ Repl(invert_q_m, 8),q_m[8], invert_q_m))
        with m.If(self.CD[1] == 1):
            with m.If(self.CD[0]):
                m.d.comb += TMDS_code.eq(0b1010101011)
            with m.Else():
                m.d.comb += TMDS_code.eq(0b0101010100)
        with m.Else():
            with m.If(self.CD[0]):
                m.d.comb += TMDS_code.eq(0b0010101011)
            with m.Else():
                m.d.comb += TMDS_code.eq(0b1101010100)

        with m.If(self.VDE):
            m.d.clk_25MHz += self.TMDS.eq(TMDS_data)
            m.d.clk_25MHz += balance_acc.eq(balance_acc_new)
        with m.Else():
            m.d.clk_25MHz += self.TMDS.eq(TMDS_code)
            m.d.clk_25MHz += balance_acc.eq(0b0000)
        
  

        return m



if __name__ == "__main__":
    platform = Colorlighti5R70ExtensionBoardPlatform()

        
    hdmi = Hdmi(Signal(1), # 0 i_reset
                Signal(8), # 1 i_red
                Signal(8), # 2 i_grn
                Signal(8), # 3 i_blu
                Signal(1), # 4 o_rd
                Signal(1), # 5 o_newline
                Signal(1), # 6 o_newframe
                Signal(1), # 7 o_red
                Signal(1), # 8 o_grn
                Signal(1)) # 9 o_blu
                # clk 250
                # rst clk 250
                # clk 25
                # rst clk 25
    with open("hdmi.v", "w") as f:
        f.write(verilog.convert(hdmi, 
            ports=[hdmi.i_reset, hdmi.i_red, hdmi.i_grn, hdmi.i_blu, 
            hdmi.o_rd, hdmi.o_newline, hdmi.o_newframe, 
            hdmi.o_red, hdmi.o_grn, hdmi.o_blu]))


