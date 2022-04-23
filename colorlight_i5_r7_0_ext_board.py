import os
import subprocess

from amaranth.build import *
from amaranth.vendor.lattice_ecp5 import *
from amaranth_boards.resources import *



__all__ = ["Colorlighti5R70ExtensionBoardPlatform"]


class Colorlighti5R70ExtensionBoardPlatform(LatticeECP5Platform):
    """
    The Colorlight i5 r7.0 is often paired with an extension develpmnet board
    which provides an ample set of I/O.

    Official documentation of Colorlight i5 r7.0 and extension board:
    https://github.com/wuxx/Colorlight-FPGA-Projects

    The extension board schematic:
    https://github.com/wuxx/Colorlight-FPGA-Projects/blob/master/schematic/i5_v6.0-extboard.pdf

    Tom Verbeure FPGA pin to connector on extension board mapping diagram:
    https://tomverbeure.github.io/assets/colorlight_i5/colorlight_i5_ext_board_pin_mapping.pdf
    """

    device                 = "LFE5U-25F"
    package                = "BG381"
    speed                  = "6"
    default_clk            = "clk25"

    resources = [
        Resource("clk25", 0, Pins("P3", dir="i"), Clock(25e6), Attrs(IO_TYPE="LVCMOS33")),

        *LEDResources(pins="U16", invert = True, attrs=Attrs(IO_TYPE="LVCMOS33", DRIVE="4")),

        UARTResource(0,
            tx="H18",
            rx="J17",
            attrs=Attrs(IO_TYPE="LVCMOS33")
        ),

        Resource("hdmi_tx", 0,
            Subsignal("clk", DiffPairs("J19", "K19", dir="o"),
                Attrs(IOSTANDARD="TMDS_33")),
            Subsignal("d",   DiffPairs("G19 E20 C20", "H20 F19 D19", dir="o"),
                Attrs(IOSTANDARD="TMDS_33")),
            Attrs(IOSTANDARD="LVCMOS33")),



    ]

    connectors = [
        Connector("pmod", 0, "M17 R17 T18 K18 - - P17 R18 C18 U16 - -"),  # P2A
        Connector("pmod", 1, "G20 K20 L20 N18 - - J20 L18 M18 N17 - -"),  # P2B
        Connector("pmod", 2, "A18 A19 B19 D20 - - C17 B18 B20 F20 - -"),  # P3A
        Connector("pmod", 3, "E2  D2  B1  A3  - - D1  C1  C2  E3  - -"),  # P3B
        Connector("pmod", 4, "H3  F3  E4  E1  - - H4  G3  F1  F2  - -"),  # P4A
        Connector("pmod", 5, "-   B2  K4  A2  - - -   E19 B3  K5  - -"),  # P4B
        Connector("pmod", 6, "D17 D16 E6  F4  - - D18 G5  F5  E5  - -"),  # P5A
        Connector("pmod", 7, "H18 G18 F18 E18 - - J17 H17 H16 G16 - -"),  # P5B
        Connector("pmod", 8, "N4  L4  P16 J18 - - R3  M4  L5  J16 - -"),  # P6A
        Connector("pmod", 9, "T1  Y2  V1  N2  - - R1  U1  W1  M1  - -"),  # P6B

        Connector("gpio", 0, {
            "P2_7" : "U18", "P2_9" : "P18", "P2_22" : "U17", "P2_24" : "T17", # P2
            "P3_7" : "C4" , "P3_9" : "C3" , "P3_22" : "B4" , "P3_24" : "D3" , # P3
            "P4_7" : "H5" , "P4_9" : "J5" , "P4_22" : "K3" , "P4_24" : "J4" , # P4
            "P5_7" : "E17", "P5_9" : "E16", "P5_22" : "F17", "P5_24" : "E16", # P5
            "P6_7" : "T3" , "P6_9" : "T2" , "P6_22" : "N3" , "P6_24" : "M3" , # P6
        }),
    ]

    @property
    def required_tools(self):
        return super().required_tools + [
            "openFPGALoader"
        ]

    def toolchain_prepare(self, fragment, name, **kwargs):
        overrides = dict(ecppack_opts="--compress")
        overrides.update(kwargs)
        return super().toolchain_prepare(fragment, name, **overrides)

    def toolchain_program(self, products, name):
        tool = os.environ.get("OPENFPGALOADER", "openFPGALoader")
        with products.extract("{}.bit".format(name)) as bitstream_filename:
            subprocess.run([tool, "-c", "cmsisdap", "-m", bitstream_filename])


