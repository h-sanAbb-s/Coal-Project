from time import sleep
import inspect
import threading


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
        self.PSR = {'S': 0, 'A1' : 0, 'A0' : 0, 'E': 0, 'AC': 0, 'PC': 0, 'PC0':0}

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


        self.running = False
        self.execute = False
        self.stepping = False
        self.lock = threading.Lock()
        self.ui = None
        self.update_ui = False 

        # Main Memory (256 words, each 12 bits)
        self.main_memory = [''] * 256

        # Secondary Memory (8 rows, 7 columns)
        # Each row represents a tuple: (S, A1, A0, E, AC, PC0, PC)
        self.secondary_memory = [
            {'S': '', 'A1' : '', 'A0' : '', 'E': '', 'AC': '', 'PC0': '', 'PC': ''} for _ in range(8)
        ]

        self.changed_vars = []
        ## OTHER GLOBAL VARIABLE
        self.instruction_map = {
            "AND": self.AND_instruction,
            "ADD": self.ADD_instruction,
            "SUB": self.SUB_instruction,
            "OR": self.OR_instruction,
            "CAL": self.CAL_instruction,
            "LDA": self.LDA_instruction,
            "STA": self.STA_instruction,
            "BR": self.BR_instruction,
            "ISA": self.ISA_instruction,
            "SWT": self.SWT_instruction,
            "AWT": self.AWT_instruction,
            "CLE": self.CLE_instruction,
            "CMA": self.CMA_instruction,
            "CME": self.CME_instruction,
            "CIR": self.CIR_instruction,
            "CIL": self.CIL_instruction,
            "SZA": self.SZA_instruction,
            "SZE": self.SZE_instruction,
            "ICA": self.ICA_instruction,
            "ESW": self.ESW_instruction,
            "DSW": self.DSW_instruction,
            "HLT": self.HLT_instruction,
            "FORK": self.FORK_instruction,
            "RST": self.RST_instruction,
            "UTM": self.UTM_instruction,
            "LDP": self.LDP_instruction,
            "SPA": self.SPA_instruction,
            "INP": self.INP_instruction,
            "OUT": self.OUT_instruction,
            "SKI": self.SKI_instruction,
            "SKO": self.SKO_instruction,
            "EI": self.EI_instruction,
        }


    def fetch(self):
        self.AR = self.PC
        self.block(['AR']) 
        self.IR = self.main_memory[int(self.AR, 16)]
        self.PC = self.hex_op(self.PC, '1', bits = 2) 
        self.block(['IR', 'PC'])

    def decode(self):
        codes = self.IR.split(' ')
        if len(codes) == 1:
            self.block()
            return codes[0].strip().upper(), None,False
        elif len(codes) == 2:
            self.AR = codes[-1].upper().strip()
            self.block(['AR'])
            return codes[0],codes[-1].upper(),False
        else:
            self.AR = codes[-1]
            self.I = 1
            self.block(['AR'])
            return codes[0].strip().upper(),codes[-1].strip().upper,True

    @staticmethod
    def hex_op(hex1, hex2, bits = 3, func = lambda x, y : x + y): 
        if bits == 3: 
            return f"{func(int(hex1, 16), int(hex2, 16)):03x}".upper()

        if bits == 2: 
            return f"{func(int(hex1, 16), int(hex2, 16)):02x}".upper()
    
    @staticmethod
    def minus(x, y): return x - y

    def block(self, changed_var = []): 
        self.changed_vars = changed_var
        self.update_ui = True
        with self.lock: 
            self.execute = False 

        if self.running:
            sleep(1/self.clk) 
        else: 
            while self.execute == False: pass

        print(f"comming out of block with parent function {inspect.stack()[1].function}")


    def contextSwitch(self):
        self.PSR["PC"] = self.PC
        self.PSR["AC"] = self.AC
        self.PSR["E"] = self.E
        self.PSR["A0"] = self.A0
        self.PSR["A1"] = self.A1
        self.PSR["S"] = self.S
        self.AR = self.PRC
        self.block(['AR', 'PRC'])

        self.TAR = self.main_memory[int(self.AR, 16)]
        self.block(['TAR'])

        self.AR = '08'
        self.PRC = self.hex_op(self.PRC,  '1', 2)
        self.block(['AR', 'PRC'])

        self.secondary_memory[int(self.TAR, 16)] = self.PSR
        self.TM = self.main_memory[int(self.AR, 16)]
        if (self.PRC == self.TP):
            self.PRC = '000'
        self.block(['PRC', 'TM'])        

        self.AR = self.PRC
        self.block(['AR'])

        self.TAR = self.main_memory[int(self.AR, 16)]
        self.block(['TAR'])

        self.PSR = self.secondary_memory[int(self.TAR, 16)]
        self.block(['PSR'])

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
        self.block(['PC', 'AC', 'E', 'A0', 'A1', 'S', 'C'])

    def CAL_instruction(self):
        self.DR = self.main_memory[int(self.AR, 16)]
        self.block(['DR'])

        if self.A0 == 0 and self.A1 == 0:
            self.AC = self.hex_op(self.AC, self.DR)
        elif self.A0 == 1 and self.A1 == 0:
            self.AC = self.hex_op(self.AC, self.DR, func = self.minus)
        elif self.A0 == 0 and self.A1 == 1:
            self.AC = self.hex_op(self.AC, self.DR, func = lambda x,y: x & y)
        else:
            self.AC = self.hex_op(self.AC, self.DR, func = lambda x,y: x | y)

        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['AC', 'TM'])

    def LDA_instruction(self):
        self.DR = self.main_memory[int(self.AR, 16)]
        self.block(['DR'])

        self.AC = self.DR
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['AC', 'SC', 'TM'])

    def STA_instruction(self):
        self.main_memory[int(self.AR, 16)] = self.AC
        self.block()

        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['TM'])


    def BR_instruction(self):
        self.PC = self.AR
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2)  

        self.block(['PC', 'TM', 'SC'])

    def ISA_instruction(self):
        self.DR = self.main_memory[int(self.AR, 16)]
        self.block(['DR'])

        self.DR = self.hex_op(self.DR, '1', func = self.minus)
        self.block(['DR'])

        self.main_memory[int(self.AR, 16)] = self.DR
        if self.DR == self.AC:
            self.PC = self.hex_op(self.PC, '1', bits = 2) 
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['DR', 'PC', 'TM', 'SC'])

    def SWT_instruction(self):
        self.PSR["PC"] = self.PC
        self.PSR["AC"] = self.AC
        self.PSR["E"] = self.E
        self.PSR["A0"] = self.A0
        self.PSR["A1"] = self.A1
        self.PSR["S"] = self.S
        
        self.TR = self.main_memory[int(self.AR, 16)]
        self.block(['PSR', 'TR'])

        self.AR = self.PRC
        self.block(['AR'])

        self.TAR = self.main_memory[int(self.AR, 16)]
        self.block(['TAR'])

        self.secondary_memory[int(self.TAR, 16)] = self.PSR
        self.TAR = self.TR
        self.block(['TAR'])
        

        self.PSR = self.secondary_memory[int(self.TAR, 16)]
        self.AR = '08'
        self.block(['PSR', 'AR'])

        self.PC = self.PSR["PC"]
        self.AC = self.PSR["AC"]
        self.E = self.PSR["E"]
        self.A0 = self.PSR["A0"]
        self.A1 = self.PSR["A1"]
        self.S = 1
        self.TM = self.main_memory[int(self.AR, 16)]
        if self.PSR["S"] == 0:
            self.NS -= self.hex_op(self.NS, '1', func = self.minus, bits = 2) 
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['PC', 'AC', 'E', 'A0', 'A1', 'S', 'TM', 'NS', 'SC', 'TM'])
    

    def AWT_instruction(self):
        self.TAR = self.main_memory[int(self.AR, 16)]
        self.block(['TAR'])

        self.PSR = self.secondary_memory[int(self.TAR, 16)]
        self.block(['PSR'])

        if self.PSR["S"] == 1:
            self.PC = self.hex_op(self.PC, '1', func = self.minus) 
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['PC', 'SC', 'TM'])

    def CLE_instruction(self):
        self.E = 0
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['E', 'SC', 'TM'])

    def CMA_instruction(self):
        self.AC = ~self.AC & ((1 << 12) - 1)  
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['AC', 'SC', 'TM'])

    def CME_instruction(self):
        self.E = ~self.E & ((1 << 12) - 1)
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['E', 'SC', 'TM'])

    def CIR_instruction(self):

        Lsb = self.AC & 1 
        self.AC = self.hex_op(self.AC, '0', func= lambda x, y: (x >> 1) | (self.E << 11))
        self.E = Lsb
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['AC', 'E', 'SC', 'TM'])

    def CIL_instruction(self):
        Msb = (self.AC >> 11) & 1
        self.AC = self.hex_op(self.AC, '0', func= lambda x, y: ((self.AC << 1) & ((1 << 12) - 1)) | self.E)
        self.E = Msb
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['AC', 'E', 'SC', 'TM'])


    def SZA_instruction(self):
        if self.AC == 0:
            self.PC = self.hex_op(self.PC, '1', bits = 2) 
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['PC', 'SC', 'TM'])

    def SZE_instruction(self):
        if self.E == 0:
            self.PC = self.hex_op(self.PC, '1', bits = 2)     
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['PC', 'SC', 'TM'])

    def ICA_instruction(self):
        self.AC += self.hex_op(self.TM, '1')
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['AC', 'SC', 'TM'])

    def ESW_instruction(self):
        self.SW = 1
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['SW', 'SC', 'TM'])

    def DSW_instruction(self):
        self.SW = 0
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['SW', 'SC', 'TM'])
    
    def ADD_instruction(self):
        self.A0 = 0
        self.A1 = 0
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['A0', 'A1', 'SC', 'TM'])
    
    def SUB_instruction(self):
        self.A0 = 1
        self.A1 = 0
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['A0', 'A1', 'TM', 'SC']) 

    def AND_instruction(self):
        self.A0 = 0
        self.A1 = 1
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['A0', 'A1', 'TM', 'SC'])

    def OR_instruction(self):
        self.A0 = 1
        self.A1 = 1
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['A0', 'A1', 'TM', 'SC'])

    def HLT_instruction(self):
        self.S = 0
        self.NS = self.hex_op(self.NS, '1', bits = 2)
        self.block(['S', 'NS'])

        if self.NS == self.TP:
            self.GS = 0
        self.S = 0
        self.PC = self.hex_op(self.PC, '1', funct=self.minus, bits=2)
        self.C = 1
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['S', 'GS', 'PC', 'C', 'SC', 'TM'])

    def FORK_instruction(self):
        self.PSR["PC"] = self.PC
        self.PSR["AC"] = self.AC
        self.PSR["E"] = self.E
        self.PSR["A0"] = self.A0
        self.PSR["A1"] = self.A1
        self.PSR["S"] = self.S
        self.AR = self.TP
        self.TP = self.hex_op(self.TM, '1', bits = 2) 
        self.block(['PSR', 'AR', 'TP'])


        self.TAR = self.main_memory[int(self.AR, 16)]
        self.block(['TAR'])

        self.secondary_memory[int(self.TAR, 16)] = self.PSR
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['SC', 'TM'])

    def RST_instruction(self):
        self.AR = self.PRC
        self.block(['AR'])
        
        self.TAR =  self.main_memory[int(self.AR, 16)]
        self.block(['TAR'])

        self.PSR = self.secondary_memory[int(self.TAR, 16)]
        self.block(['PSR'])

        self.PSR["PC"] = self.PSR["PC0"]
        self.PSR["AC"] = '000'
        self.PSR["S"] = 0
        self.PSR["A0"] = 0
        self.PSR["A1"] = 0
        self.PSR["E"] = 0
        self.S = 0
        self.SC = 0
        self.C = 1
        self.block(['PSR', 'S', 'SC'])


    def UTM_instruction(self):
        self.AR = '08'
        self.block(['AR'])
        self.TM = self.main_memory[int(self.AR, 16)]
        self.SC = 0
        self.block(['TM', 'SC'])

    def LDP_instruction(self):
        self.AR = self.PRC
        self.block(['AR'])

        self.TAR = self.main_memory[int(self.AR, 16)]
        self.block(['TAR'])

        self.PSR = self.secondary_memory[int(self.TAR, 16)]
        self.block(['PSR'])

        self.PC = self.PSR["PC"]
        self.AC = self.PSR["AC"]
        self.E = self.PSR["E"]
        self.A0 = self.PSR["A0"]
        self.A1 = self.PSR["A1"]
        self.S = self.PSR["S"]
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['PC', 'AC', 'A0', 'A1', 'S', 'E', 'SC', 'TM'])

    def SPA_instruction(self):
        self.AR = self.PRC
        self.block(['AR'])

        if self.main_memory[int(self.AR, 16)] == self.AC:
            self.PC = self.hex_op(self.PC, '1', bits = 2) 

        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['SC', 'TM'])

    def INP_instruction(self):
        self.AC = self.INPR
        self.FGI = 0
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['AC', 'FGI', 'SC', 'TM'])
    
    def OUT_instruction(self):
        self.OUTR = self.AC
        self.FGO = 0
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['OUTR', 'FGO', 'SC', 'TM'])

    def SKI_instruction(self):
        if self.FGI == 1:
            self.PC = self.hex_op(self.PC, '1', bits = 2) 
        
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['PC', 'SC', 'TM'])

    def SKO_instruction(self):
        if self.FGO == 1:
            self.PC = self.hex_op(self.PC, '1', bits = 2) 
        
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['PC', 'SC', 'TM'])

    def EI_instruction(self):
        self.IEN = 1
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['IEN', 'SC', 'TM'])

    def DI_instruction(self):
        self.IEN = 0
        self.SC = 0
        self.TM = self.hex_op(self.TM, '1', func = self.minus, bits = 2) 
        self.block(['IEN', 'SC', 'TM'])


    def run_next(self):
        self.stepping = True
        if self.TM == '00':
                self.C = 1
                self.contextSwitch()
        else:
            self.fetch()
            opcode, address, I_address = self.decode()
            if I_address == True:
                self.AR = self.main_memory[address]
                self.block(['AR'])
            
            if opcode in self.instruction_map:
                self.instruction_map[opcode]()  
            else:
                raise ValueError(f"Unknown opcode: {opcode}")
        
        self.stepping = False
      