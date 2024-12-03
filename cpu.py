import time

class CPU:
    def __init__(self):
        self.AR = '0'     # Address Register (8 bits)
        self.PC = '0'     # Program Counter (8 bits)
        self.DR = '0'     # Data Register (12 bits)
        self.AC = '0'     # Accumulator (12 bits)
        self.INPR = '0'   # Input Register (8 bits)
        self.IR = '0'     # instruction Register (12 bits)
        self.TR = '0'     # Temporary Register (12 bits)
        self.TM = '0'     # Timer Register (8 bits)
        self.PRC = '0'    # Priority Register (3 bits)
        self.TAR = '0'    # Target Register (3 bits)
        self.TP = '0'     # Temporary Pointer (3 bits)
        self.NS = '0'     # Next State Register (3 bits)
        self.OUT = '0'    # Output Register (8 bits)
        self.PSR = '0'

        # Flip-Flops
        self.I = 0      # Interrupt Flip-Flop
        self.E = 0      # Enable Flip-Flop
        self.R = 0      # Read Flip-Flop
        self.C = 0      # Carry Flip-Flop
        self.SW = 0     # Switch Flip-Flop
        self.IEN = 0    # Interrupt Enable Flip-Flop
        self.FGI = 0    # Input Flag
        self.FGO = 0    # Output Flag
        self.S = 0      # Start Flip-Flop
        self.GS = 0     # General Status Flip-Flop
        self.A0 = 0     # A0 Flip-Flop
        self.A1 = 0     # A1 Flip-Flop
        self.clk = 1

        # Main Memory (256 words, each 12 bits)
        self.main_memory = [''] * 256

        # Secondary Memory (8 rows, 7 columns)
        # Each row represents a tuple: (S, A1, A0, E, AC, PC0, PC)
        self.secondary_memory = [
            {'S': '', 'A1' : '', 'A0' : '', 'E': '', 'AC': '', 'PC0': '', 'PC': ''} for _ in range(8)
        ]
    def fetch(self):
        self.AR = self.PC
        self.IR = self.main_memory[int(self.AR)]
        self.PC += 1

    def decode(self):
        codes = self.IR.split(' ')
        if len(codes) == 1:
            return {"instruction":codes[0],"address":None,"I_addressing":False}
        elif len(codes) == 2:
            self.AR = codes[-1]
            return {"instruction":codes[0],"address":codes[-1],"I_addressing":False}
        else:
            self.AR = codes[-1]
            self.I = 1
            return {"instruction":codes[0],"address":codes[-1],"I_addressing":True}
    
    def contextSwitch(self):
        self.PSR["PC"] = self.PC
        self.PSR["AC"] = self.AC
        self.PSR["E"] = self.E
        self.PSR["A0"] = self.A0
        self.PSR["A1"] = self.A1
        self.PSR["S"] = self.S
        self.AR = self.PRC
        self.TAR = self.main_memory[int(self.AR)]
        self.AR = 8
        self.PRC += 1
        self.secondary_memory[int(self.TAR)] = self.PSR
        self.TM = self.main_memory[int(self.AR)]
        if (self.PRC == self.TP):
            self.PRC = 0
        self.AR = self.PRC
        self.TAR = self.main_memory[int(self.AR)]
        self.PSR = self.secondary_memory[int(self.TAR)]
        self.PC = self.PSR["PC"]
        self.AC = self.PSR["AC"]
        self.E = self.PSR["E"]
        self.A0 = self.PSR["A0"]
        self.A1 = self.PSR["A1"]
        self.S = self.PSR["S"]
        self.C = 0
        if (self.S == 0):
            self.C = 1
        self.SC = 0

    def CAL_instruction(self):
        self.DR = self.main_memory[int(self.AR)]
        if self.A0 == 0 and self.A1 == 0:
            self.AC = self.AC + self.DR
        elif self.A0 == 1 and self.A1 == 0:
            self.AC = self.AC - self.DR
        elif self.A0 == 0 and self.A1 == 1:
            self.AC = self.AC & self.DR
        else:
            self.AC = self.AC | self.DR

        self.TM -= 1

    def LDA_instruction(self):
        self.DR = self.main_memory[int(self.AR)]
        self.AC = self.DR
        self.SC = 0
        self.TM -= 1

    def STA_instruction(self):
        self.main_memory[int(self.AR)] = self.AC
        self.SC = 0
        self.TM -= 1

    def BR_instruction(self):
        self.PC = self.AR
        self.SC = 0
        self.TM -= 1

    def ISA_instruction(self):
        self.DR = self.main_memory[int(self.AR)]
        self.DR += 1
        self.main_memory[int(self.AR)] = self.DR
        if self.DR == self.AC:
            self.PC += 1
        self.SC = 0
        self.TM -= 1

    def SWT_instruction(self):
        self.PSR["PC"] = self.PC
        self.PSR["AC"] = self.AC
        self.PSR["E"] = self.E
        self.PSR["A0"] = self.A0
        self.PSR["A1"] = self.A1
        self.PSR["S"] = self.S
        self.TR = self.main_memory[int(self.AR)]
        self.AR = self.PRC
        self.TAR = self.main_memory[int(self.AR)]
        self.secondary_memory[int(self.TAR)] = self.PSR
        self.TAR = self.TR
        self.PSR = self.secondary_memory[int(self.TAR)]
        self.AR = 8
        self.PC = self.PSR["PC"]
        self.AC = self.PSR["AC"]
        self.E = self.PSR["E"]
        self.A0 = self.PSR["A0"]
        self.A1 = self.PSR["A1"]
        self.S = 1
        self.TM = self.main_memory[int(self.AR)]
        if self.PSR["S"] == 0:
            self.NS -= 1
        self.SC = 0
        self.TM -= 1
    

    def AWT_instruction(self):
        self.TAR = self.main_memory[int(self.AR)]
        self.PSR = self.secondary_memory[int(self.TAR)]
        if self.PSR["S"] == 1:
            self.PC += 1
        self.SC = 0
        self.TM -= 1

    def CLE_instruction(self):
        self.E = 0
        self.SC = 0
        self.TM -= 1

    def CMA_instruction(self):
        self.AC = ~self.AC & ((1 << 12) - 1)  
        self.SC = 0
        self.TM -= 1

    def CME_instruction(self):
        self.E = ~self.E & ((1 << 12) - 1)
        self.SC = 0
        self.TM -= 1

    def CIR_instruction(self):

        Lsb= self.AC & 1 
        self.AC = (self.AC >> 1) | (self.E << 11) 
        self.E = Lsb
        self.SC = 0
        self.TM -= 1

    def CIL_instruction(self):
        Msb = (self.AC >> 11) & 1
        self.AC = ((self.AC << 1) & ((1 << 12) - 1)) | self.E  
        self.E = Msb
        self.SC = 0
        self.TM -= 1


    def SZA_instruction(self):
        if self.AC == 0:
            self.PC += 1
        self.SC = 0
        self.TM -= 1
    def SZE_instruction(self):
        if self.E == 0:
            self.PC += 1    
        self.SC = 0
        self.TM -= 1
    def ICA_instruction(self):
        self.AC += 1
        self.SC = 0
        self.TM -= 1

    def ESW_instruction(self):
        self.SW = 1
        self.SC = 0
        self.TM -= 1

    def DSW_instruction(self):
        self.SW = 0
        self.SC = 0
        self.TM -= 1
    
    def ADD_instruction(self):
        self.A0 = 0
        self.A1 = 0
        self.SC = 0
        self.TM -= 1
    
    def SUB_instruction(self):
        self.A0 = 1
        self.A1 = 0
        self.SC = 0
        self.TM -= 1

    def AND_instruction(self):
        self.A0 = 0
        self.A1 = 1
        self.SC = 0
        self.TM -= 1

    def OR_instruction(self):
        self.A0 = 1
        self.A1 = 1
        self.SC = 0
        self.TM -= 1

    def HLT_instruction(self):
        self.S = 0
        self.NS += 1
        if self.NS == self.TP:
            self.GS = 0
        self.S = 0
        self.PC -= 1
        self.C = 1
        self.SC = 0
        self.TM -= 1

    def FORK_instruction(self):
        self.PSR["PC"] = self.PC
        self.PSR["AC"] = self.AC
        self.PSR["E"] = self.E
        self.PSR["A0"] = self.A0
        self.PSR["A1"] = self.A1
        self.PSR["S"] = self.S
        self.AR = self.TP
        self.TP += 1
        self.TAR = self.main_memory[self.AR]
        self.secondary_memory[self.TAR] = self.PSR
        self.SC = 0
        self.TM -= 1

    def RST_instruction(self):
        self.AR = self.PRC
        self.TAR =  self.main_memory[self.AR]
        self.PSR = self.secondary_memory[self.TAR]
        self.PSR["PC"] = self.PSR["PC0"]
        self.PSR["AC"] = 0
        self.PSR["S"] = 0
        self.PSR["A0"] = 0
        self.PSR["A1"] = 0
        self.PSR["E"] = 0
        self.S = 0
        self.SC = 0


    def UTM_instruction(self):
        self.AR = 8
        self.TM = self.main_memory[self.AR]
        self.SC = 0
        self.TM -= 1

    def LDP_instruction(self):
        self.AR = self.PRC
        self.TAR = self.main_memory[int(self.AR)]
        self.PSR = self.secondary_memory[int(self.TAR)]
        self.PC = self.PSR["PC"]
        self.AC = self.PSR["AC"]
        self.E = self.PSR["E"]
        self.A0 = self.PSR["A0"]
        self.A1 = self.PSR["A1"]
        self.S = self.PSR["S"]
        self.SC = 0
        self.TM -= 1

    def SPA_instruction(self):
        self.AR = self.PRC
        if self.main_memory[self.AR] == self.AC:
            self.PC += 1

        self.SC = 0
        self.TM -= 1

    def INP_instruction(self):
        self.AC = self.INPR
        self.FGI = 0
        self.SC = 0
        self.TM -= 1
    
    def OUT_instruction(self):
        self.OUTR = self.AC
        self.FGO = 0
        self.SC = 0
        self.TM -= 1

    def SKI_instruction(self):
        if self.FGI == 1:
            self.PC += 1
        
        self.SC = 0
        self.TM -= 1

    def SKO_instruction(self):
        if self.FGO == 1:
            self.PC += 1
        
        self.SC = 0
        self.TM -= 1

    def EI_instruction(self):
        self.IEN = 1
        self.SC = 0
        self.TM -= 1

    def DI_instruction(self):
        self.IEN = 0
        self.SC = 0
        self.TM -= 1

    def test(self): 
        self.GS = 1
        time.sleep(2)
        self.PC = '18'
        time.sleep(2)
        self.AR = '20'