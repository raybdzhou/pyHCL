"""Simulator sources

Filename: sim_src.py
Author: SunnyChen
"""

import mmap, os

# Backend config
import time
from inspect import getmodule

from pyhcl import *

psize = 4096
uint64_t_size = 8
input_signum = 0
output_signum = 0

# Signals
WAIT = 0
DOUT = 1
DIN  = 2
TERM = 3
STEP = 4
START = 5
RESET = 6


def read_data(mm):
    rdata = int.from_bytes(mm.read(uint64_t_size), "little")
    mm.seek(0)
    return rdata


def write_data(mm, value):
    mm.write(int(value).to_bytes(uint64_t_size, "little"))
    mm.seek(0)


def search_io(io, input_sig_map, output_sig_map):
    global input_signum, output_signum
    for k in io.__dict__:
        if not k.startswith("_") and not k.startswith("__"):
            obj = io.__dict__[k]
            if isinstance(obj, Bundle):
                search_io(obj, input_sig_map, output_sig_map)
            elif isinstance(obj, Input):
                input_sig_map[obj] = input_signum
                input_signum += 1
            elif isinstance(obj, Output):
                output_sig_map[obj] = output_signum
                output_signum += 1


def select_datawrapper(width):
    if 1 <= width <= 8:
        return "CDataWrapper"
    elif 9 <= width <= 16:
        return "SDataWrapper"
    elif 17 <= width <= 32:
        return "IDataWrapper"
    elif 33 <= width <= 64:
        return "QDataWrapper"


def push_data(input_sig_map, output_sig_map):
    cat_table = []
    for k in input_sig_map.keys():
        width = k._define_node.type.width
        if width <= 0:
            raise ValueError("Simulate IO ports must specified width")

        datawrapper = select_datawrapper(width)
        port_name = "_".join(k._data._ir_exp.emit().split("."))
        cat_table.append(
            "\t\tthis->sim_datas.inputs.push_back(new {datawrapper}(&(dut->{name})));\n".format(datawrapper=datawrapper,
                                                                                                name=port_name))

    for k in output_sig_map.keys():
        width = k._define_node.type.width
        if width <= 0:
            raise ValueError("Simulate IO ports must specified width")

        datawrapper = select_datawrapper(width)
        port_name = "_".join(k._data._ir_exp.emit().split("."))
        cat_table.append(
            "\t\tthis->sim_datas.outputs.push_back(new {datawrapper}(&(dut->{name})));\n".format(datawrapper=datawrapper,
                                                                                                name=port_name))
    return "".join(cat_table)

class Simulator(object):
    def __init__(self, module):
        # Cat table of the harness code string
        cat_table = []

        # Pipe channel open in channel init
        self.mm_in = None
        self.mm_sig = None
        self.mm_out = None

        self.input_sig_map = {}
        self.output_sig_map = {}
        self.dut_name = module.__class__.__name__
        self.step_count = 0

        global input_signum
        # Push clock and reset
        self.input_sig_map[module.clock] = input_signum
        input_signum += 1
        self.input_sig_map[module.reset] = input_signum
        input_signum += 1

        # Recursively search bundle
        for k in module.__dict__:
            obj = module.__dict__[k]
            if isinstance(obj, Bundle):
                search_io(obj, self.input_sig_map, self.output_sig_map)


        # Generate cpp harness code
        harness_code_A = """#include \"V{name}.h\"
#include \"simulator.h\"
using namespace std;

class {name}_Simulator: public Simulator<DataWrapper*>
{{
private:
    V{name}* dut;
    VerilatedVcdC *tfp;
    int psize;

public:
    {name}_Simulator(V{name}* _dut): Simulator()
    {{
        this->dut = _dut;
        this->psize = getpagesize();
    }}

    ~{name}_Simulator()
    {{
        munmap(this->in, this->psize);
        munmap(this->sig, this->psize);
        munmap(this->out, this->psize);
        close(this->in_fd);
        close(this->out_fd);
        close(this->sig_fd);
        remove("./in.dat");
        remove("./sig.dat");
        remove("./out.dat");
    }}

    void init_tfp(VerilatedVcdC *_tfp)
    {{
        this->tfp = _tfp;
    }}

    void init_simdata()
    {{
        this->sim_datas.inputs.clear();
        this->sim_datas.outputs.clear();

""".format(name=self.dut_name)

        cat_table.append(harness_code_A)

        push_str = push_data(self.input_sig_map, self.output_sig_map)
        cat_table.append(push_str)
        
        harness_code_B = """\t}}

    virtual void step()
    {{
        this->dut->clock = 0;
        this->dut->eval();
        this->tfp->dump((vluint64_t)this->main_time);
        this->main_time++;

        this->dut->clock = 1;
        this->dut->eval();
        this->tfp->dump((vluint64_t)this->main_time);
        this->main_time++;
    }}

    virtual void reset()
    {{
        this->dut->reset = 1;
        step();
    }}

    virtual void start()
    {{
        this->dut->reset = 0;
        step();
    }}
}};

int main(int argc, char **argv)
{{
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);
    V{name} *top = new V{name};
    VerilatedVcdC *tfp = new VerilatedVcdC;
    tfp = new VerilatedVcdC;
    top->trace(tfp, 99);
    tfp->open("{name}.vcd");
    {name}_Simulator sim(top);
    sim.init_simdata();
    sim.init_tfp(tfp);
    
    top->reset = 1;

    while(!sim.isexit())
        sim.tick();

    delete tfp;
    delete top;
    exit(0);
}}        
        """.format(name=self.dut_name)
        cat_table.append(harness_code_B)

        harness_code = "".join(cat_table)

        try:
            os.mkdir("simulation")
        except FileExistsError:
            pass
        with open("./simulation/{}-harness.cpp".format(self.dut_name), "w+") as harness_file:
            harness_file.write(harness_code)

        builder.emit(builder.elaborate(module), "./simulation/{}.fir".format(self.dut_name))
        builder.dumpverilog("./simulation/{}.fir".format(self.dut_name), "./simulation/{}.v".format(self.dut_name))

        vfn = "{}.v".format(self.dut_name)
        hfn = "{}-harness.cpp".format(self.dut_name)
        mfn = "V{}.mk".format(self.dut_name)
        efn = "V{}".format(self.dut_name)

        src_file = "/".join(getmodule(Simulator).__file__.split("/")[:-1]) + "/src/simulator.h"
        os.system("cp {} ./simulation".format(src_file))

        # Using verilator backend
        os.chdir("./simulation")
        os.system("verilator --cc {vfn} --trace --exe {hfn}".format(vfn=vfn, hfn=hfn))
        os.system("make -j -C ./obj_dir -f {mfn} {efn}".format(mfn=mfn, efn=efn))

        # Run simulation backend program
        os.system("./obj_dir/{}&".format(efn))

        time.sleep(1)

        self.init_channel()

    def init_channel(self):
        self.mm_in = mmap.mmap(os.open("./in.dat", os.O_RDWR), psize)
        self.mm_sig = mmap.mmap(os.open("./sig.dat", os.O_RDWR), psize)
        self.mm_out = mmap.mmap(os.open("./out.dat", os.O_RDWR), psize)

    def wait_signal(self):
        signal = read_data(self.mm_sig)
        while signal != WAIT:
            signal = read_data(self.mm_sig)

    def poke(self, port, value):
        signum = self.input_sig_map[port]
        # print(signum)

        self. wait_signal()
        write_data(self.mm_in, value)
        self.mm_in.seek(uint64_t_size)
        write_data(self.mm_in, signum)
        write_data(self.mm_sig, DIN)
        print("{}->".format(port._data._ir_exp.emit()), value)

    def peek(self, port):
        signum = self.output_sig_map[port]
        # print(signum)

        self.wait_signal()
        self.mm_out.seek(uint64_t_size)
        write_data(self.mm_out, signum)
        write_data(self.mm_sig, DOUT)
        self.wait_signal()
        print("{}->".format(port._data._ir_exp.emit()), read_data(self.mm_out))

    def step(self):
        self.wait_signal()
        write_data(self.mm_sig, STEP)
        print("step %d" % self.step_count)
        self.step_count += 1

    def term(self):
        self.wait_signal()
        write_data(self.mm_sig, TERM)
        time.sleep(1)
        os.remove("./in.dat")
        os.remove("./out.dat")
        os.remove("./sig.dat")

    def start(self):
        write_data(self.mm_sig, START)

    def reset(self):
        write_data(self.mm_sig, RESET)
