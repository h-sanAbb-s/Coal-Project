import tkinter as tk
from tkinter import ttk, filedialog
from cpu import CPU
import yaml
import threading
import time

class UI:
    def __init__(self, cpu: CPU):
        self.cpu = cpu

        # Main Window
        self.root = tk.Tk()
        self.root.title("Basic Computer Simulation")

        # Running text and request
        self.run_button_text = tk.StringVar(value="Run")
        self.stop_requested = False

        # self.root.geometry("800x600")
        self.registers_names = ["AR", "PC", "DR", "AC", "INPR", "IR", "TR", "TM", "PRC", "TAR", "TP", "NS", "OUT", "PSR"]
        self.flip_flops_names = ["I", "E", "R", "C", "SW", "IEN", "FGI", "FGO", "S", "GS", "A0", "A1"]
        self.prev_state = {}
        # self.prev_changed_values = self.registers_names + self.flip_flops_names
        self.prev_changed_values = [] 
        self.loading = False
        # self.cpu.set_ui(self)

        memory_frame = tk.Frame(self.root)
        memory_frame.pack(anchor=tk.W)
        # Main Memory Table
        self.create_main_memory_table(memory_frame)

        # Flip-Flops Panel
        self.create_flip_flops_panel(memory_frame)

        # Registers Panel
        self.create_registers_panel(memory_frame)

        smf = tk.Frame(memory_frame)
        smf.pack(side=tk.LEFT, anchor=tk.N)
        # Secondary Memory Table
        self.create_secondary_memory_table(smf)
        self.create_buttons(smf)

        # Start the main loop
        self.ui_loop()
        self.update_ui()
        self.root.mainloop()


    def step_code(self):
        if self.cpu.stepping == False: 
            # self.prev_changed_values = self.registers_names + self.flip_flops_names
            # self.clear_selected()
            self.step_running = threading.Thread(target = self.cpu.run_next,daemon=True)
            self.step_running.start()

        else: 
            with self.cpu.lock: 
                self.cpu.execute = True


    def run_code(self):
        def run_instructions():
            while not self.stop_requested and self.cpu.GS != 0:
                self.cpu.run_next() 

            self.run_button_text.set("Run")
            self.running_thread = None

        if self.run_button_text.get() == "Run":
            self.stop_requested = False
            self.cpu.running = True
            self.run_button_text.set("Stop")
            self.running_thread = threading.Thread(target=run_instructions, daemon=True)
            self.running_thread.start()
        else:
            self.cpu.running = False
            self.stop_requested = True
            self.run_button_text.set("Run")


    def load_program(self): 
        exp = tk.Tk()
        exp.withdraw()  
        file_path = filedialog.askopenfilename(title="Select a file", filetypes=(("Yaml Files", "*.yaml"),))

        if file_path:
            print(f"{file_path} is loaded")
        else:
            print("No file selected")

        self.cpu.__init__()
        file = open(file_path, 'r') 
        config = yaml.safe_load(file)
        if 'REG' in config: 
            for r, v in config['REG'].items(): 
                setattr(self.cpu, r, str(v))

        if 'FF' in config: 
            for f, v in config['FF'].items(): 
                setattr(self.cpu, f, int(v))
            
        if 'M' in config: 
            for l, v in config['M'].items(): 
                l = int(str(l), 16)
                self.cpu.main_memory[l] = str(v)
        if 'M2' in config: 
            for l, p in config['M2'].items(): 
                l = int(str(l), 16)
                p['PC'] = str(p['PC'])
                p['PC0'] = str(p['PC0'])
                p['AC'] = str(p['AC'])
                self.cpu.secondary_memory[l] = p 
                    
        self.update_ui()

        # except: 
        #     print(f"Error in program file: f{file_path}")
        #     self.cpu.__init__()
        #     self.loading = False
        #     return

    

    def create_flip_flops_panel(self, frame):

        flip_flops_frame = tk.LabelFrame(frame, text="Flip-Flops", padx=10, pady=10)
        flip_flops_frame.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.W)

        self.flip_flops = {}
        for i, ff in enumerate(self.flip_flops_names):
            var = tk.StringVar(value=str(getattr(self.cpu, ff)))
            lbl = tk.Label(flip_flops_frame, text=f"{ff}:")
            lbl.grid(row = i, column= 0, pady = 1)
            entry = tk.Entry(flip_flops_frame, textvariable=var, width=10,justify='center')
            entry.grid(row = i, column = 1, pady = 1)
            entry.bind("<KeyPress>", lambda e : "break")  
            entry.bind("<KeyRelease>", lambda e: "break")  
            entry.bind("<FocusOut>", lambda e: None)  
            self.flip_flops[ff] = [var, entry]
            self.prev_state[ff] = str(getattr(self.cpu, ff))



    def create_registers_panel(self, frame):
        # Create a frame for registers
        registers_frame = tk.LabelFrame(frame, text="Registers", padx=10, pady=10)
        registers_frame.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.W)

        self.registers = {}
        for i, reg in enumerate(self.registers_names):
            width = 12 if reg != 'PSR' else 15
            if reg == 'PSR':
                psr_value = getattr(self.cpu, reg, {})
                formatted_psr = '-'.join(str(value) for key, value in psr_value.items())
                var = tk.StringVar(value=str(formatted_psr))
            else:
                var = tk.StringVar(value=str(getattr(self.cpu, reg)))

            lbl = tk.Label(registers_frame, text=f"{reg}:")
            lbl.grid(row=i, column=0, pady=1)
            entry = tk.Entry(registers_frame, textvariable=var, width=width, justify='center')
            entry.grid(row=i, column=1, pady=1)
            entry.bind("<KeyPress>", lambda e : "break")  
            entry.bind("<KeyRelease>", lambda e: "break")  
            entry.bind("<FocusOut>", lambda e: None)  
            self.registers[reg] = [var, entry]
            self.prev_state[reg] = str(getattr(self.cpu, reg))
            if reg == 'PSR': 
                self.prev_state[reg] = '-'.join(str(value) for key, value in psr_value.items())


    def create_main_memory_table(self, frame):
        # Create a frame for main memory
        f = tk.Frame(self.root)
        f.pack(side = tk.LEFT)
        main_memory_frame = tk.LabelFrame(frame, text="Main Memory", padx=10, pady=10)
        main_memory_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.main_memory_table = ttk.Treeview(main_memory_frame, columns=("Address", "Value"), show="headings", height=7)
        self.main_memory_table.heading("Address", text="Address")
        self.main_memory_table.column("Address", width=50, anchor=tk.CENTER)

        self.main_memory_table.heading("Value", text="Instructions")
        self.main_memory_table.column("Value", width=200, anchor=tk.CENTER)
        self.main_memory_table.pack(fill=tk.BOTH, expand=True)

        # Populate memory table
        for address, value in enumerate(self.cpu.main_memory):
            self.main_memory_table.insert("", "end", values=(f"{address:02x}".upper(), value))

        row_id = self.main_memory_table.get_children()[int(getattr(self.cpu, 'PC'),16)] 
        self.main_memory_table.selection_set(row_id)  
        self.main_memory_table.focus(row_id)
        self.main_memory_table.see(row_id)

    def create_secondary_memory_table(self, frame):
        # Create a frame for secondary memory
        secondary_memory_frame = tk.LabelFrame(frame, text="Secondary Memory", padx=10, pady=10)
        secondary_memory_frame.pack(side=tk.TOP)

        self.secondary_memory_table = ttk.Treeview(secondary_memory_frame, columns=("S", "A1", "A0", "E", "AC", "PC0", "PC"), show="headings", height=8)
        for col in ["S", "A1", "A0", "E", "AC", "PC0", "PC"]:
            self.secondary_memory_table.heading(col, text=col)
            self.secondary_memory_table.column(col, width=50, anchor=tk.CENTER)
        self.secondary_memory_table.pack(fill=tk.BOTH, expand=True)

        # Populate secondary memory table
        for row in self.cpu.secondary_memory:
            self.secondary_memory_table.insert("", "end", values=list(row.values()))
        
        pid = self.cpu.main_memory[int(getattr(self.cpu, 'PRC'))]
        if pid != '': 
            pid = int(pid)
            row_id = self.secondary_memory_table.get_children()[pid] 
            self.secondary_memory_table.selection_set(row_id)  
            self.secondary_memory_table.focus(row_id)
            self.secondary_memory_table.see(row_id)

    def create_buttons(self,frame): 
        # Create a frame for the buttons
        button_frame = tk.Frame(frame, padx=10, pady=10)
        button_frame.pack(expand=True, fill=tk.BOTH)

        # Configure the frame to center the buttons
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)
        # Create the buttons
        load_button = tk.Button(button_frame, text="Load", command=self.load_program)
        step_button = tk.Button(button_frame, text="Step", command=self.step_code)
        run_button = tk.Button(button_frame, text="Run", command=self.run_code)

        selected_option = tk.StringVar()
        selected_option.set(str(self.cpu.clk)+"hz")
        options = ["0.5hz", "1hz", "50hz"]
        dropdown = tk.OptionMenu(button_frame, selected_option, *options)
        dropdown.config(bg='white')
        
        # Position the buttons in the gridk
        load_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        step_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        run_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        dropdown.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        def clk_change(*args): self.cpu.clk = float(selected_option.get())
        selected_option.trace_add('write', clk_change)
    
    def ui_loop(self): 
        if cpu.update_ui: 
            start = time.perf_counter()
            # self.update_ui(selected=False)
            self.update_selected_ui()
            print(time.perf_counter() - start)
            cpu.update_ui = False
        
        self.root.after(50, self.ui_loop)
    
    def update_selected_ui(self): 
        for r in self.prev_changed_values: 
            entry = None
            if r in self.registers: 
                (_, entry) = self.registers[r]
            elif r in self.flip_flops: 
                (_, entry) = self.flip_flops[r]
            
            if entry is not None : 
                entry.config(bg='white', fg='black')

        mem_pointer = 'PC'
        for r in self.cpu.changed_vars: 
            entry = None
            if r in self.registers: 
                if self.registers == 'AR': mem_pointer = 'AC'
                (var, entry) = self.registers[r]
            elif r in self.flip_flops: 
                (var, entry) = self.flip_flops[r]
            
            if entry is not None : 
                entry.config(bg='blue', fg='white')
                var.set(getattr(self.cpu, r))
        
        self.prev_changed_values = self.cpu.changed_vars.copy()

        row_id = self.main_memory_table.get_children()[int(getattr(self.cpu, mem_pointer),16)] 
        self.main_memory_table.selection_set(row_id)  
        self.main_memory_table.focus(row_id)
        self.main_memory_table.see(row_id)

        address = getattr(self.cpu, 'PC')
        row_id = self.main_memory_table.get_children()[int(address,16)] 
        self.main_memory_table.item(row_id, values=(address, self.cpu.main_memory[int(address, 16)],))

        pid = self.cpu.main_memory[int(getattr(self.cpu, 'PRC'))]
        if pid != '': 
            pid = int(pid)
            row_id = self.secondary_memory_table.get_children()[pid] 
            self.secondary_memory_table.selection_set(row_id)  
            self.secondary_memory_table.focus(row_id)
            self.secondary_memory_table.see(row_id)

            row = self.cpu.secondary_memory[pid]
            table_id = self.secondary_memory_table.get_children()[pid]
            values = []
            for col in ["S", "A1", "A0", "E", "AC", "PC0", "PC"]:
                values.append(str(row[col]))
            self.secondary_memory_table.item(table_id, values=values)



    def clear_selected(self):
        for  _, entry in self.flip_flops.values():
            entry.config(bg='white', fg='black')

        for  _, entry in self.registers.values():
            entry.config(bg='white', fg='black')

    def update_ui(self, selected = False):
        if self.loading: return
        # if self.cpu.execute: return
        # if self.cpu.stepping: breakpoint() 

        # Update flip-flops
        for ff, (var, entry) in self.flip_flops.items():
            val = str(getattr(self.cpu,ff))
            if val != self.prev_state[ff]: 
                entry.config(bg='blue', fg='white')
                self.prev_state[ff] = val
                self.prev_changed_values.append(ff)
            else: 
                entry.config(bg='white', fg='black')
            # entry.config(state = "normal")
            var.set(val)
            # entry.config(state = "disabled")

        # Update registers
        mem_pointer = 'PC'
        for reg, (var, entry) in self.registers.items():
            val = getattr(self.cpu, reg)
            if reg == "PSR":
                val =  '-'.join(str(value) for key, value in val.items())
            else: 
                val = str(val)
            if val != self.prev_state[reg]: 
                if reg == 'AR': mem_pointer = 'AR'
                entry.config(bg='blue', fg='white')
                self.prev_state[reg] = val
                self.prev_changed_values.append(reg)
            else: 
                entry.config(bg='white', fg='black')
            var.set(val)

        # Update main memory
        row_id = self.main_memory_table.get_children()[int(getattr(self.cpu, mem_pointer),16)] 
        if int(getattr(self.cpu, 'GS')) == 1: 
            self.main_memory_table.selection_set(row_id)  
            self.main_memory_table.focus(row_id)
            self.main_memory_table.see(row_id)

        if selected: 
            address = getattr(self.cpu, 'PC')
            row_id = self.main_memory_table.get_children()[int(address,16)] 
            self.main_memory_table.item(row_id, values=(address, self.cpu.main_memory[int(address, 16)],))

        else: 
            for address, (child, value) in enumerate(zip(self.main_memory_table.get_children(), self.cpu.main_memory)):
                self.main_memory_table.item(child, values=(f"{address:02x}".upper(), value,))

        # Update secondary memory
        pid = self.cpu.main_memory[int(getattr(self.cpu, 'PRC'))]
        if pid != '': 
            pid = int(pid)
            row_id = self.secondary_memory_table.get_children()[pid] 
            if int(getattr(self.cpu, 'GS')) == 1: 
                self.secondary_memory_table.selection_set(row_id)  
                self.secondary_memory_table.focus(row_id)
                self.secondary_memory_table.see(row_id)

        for i, (child, row) in enumerate(zip(self.secondary_memory_table.get_children(), self.cpu.secondary_memory)):
            values = []
            for col in ["S", "A1", "A0", "E", "AC", "PC0", "PC"]:
                values.append(str(row[col]))
            self.secondary_memory_table.item(child, values=values)



cpu = CPU()
ui = UI(cpu)