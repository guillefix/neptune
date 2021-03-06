from ipykernel.comm import Comm
from varname import nameof
import inspect
# import threading
from multiprocessing import Process
from .mwserver import run_server, run_server_from_id
import uuid
import subprocess
import threading
# jupyter notebook --ip='*' --NotebookApp.token='' --NotebookApp.iopub_data_rate_limit=1.0e10

class Nep:
    # def __init__(self,comm_name=None):
    #     if comm_name is None:
    #         comm_name=str(uuid.uuid4())
    def __init__(self,comm=None,kernel_id=None):
        # self.comm = Comm(target_name=comm_name)
        # self.comm = Comm(target_name="neos_comm")
        print(kernel_id)
        self.kernel_id = kernel_id
        if comm is None:
            self.comm = Comm(target_name="neos_comm")
        else:
            self.comm = comm
        self.comm.open()
        self.vars = Variables(self.comm,self)
        self.comm.on_msg(self._on_msg)
        self.vars_to_update = []
        self.var_types = {}
        self.neos_updates_locked = False
        self.var_temp_vals = {}

    def start(self, base='http://localhost:8888', notebook_path='/Untitled.ipynb', auth_token='', ws_port=8766):
        if self.kernel_id is None:
            server_process = Process(target=run_server, args=(self.comm.comm_id, base, notebook_path, auth_token, ws_port),daemon=True)
        else:
            server_process = Process(target=run_server_from_id, args=(self.comm.comm_id, self.kernel_id, auth_token, ws_port),daemon=True)
        server_process.start()
        #guido forgive me coz i know this is ugly
        static_server_process = Process(target=subprocess.call, args=('python -m http.server 8000',),kwargs={"shell":True})
        static_server_process.start()

    #TODO: nep.stop() !!

    def _on_msg(self,msg):
        #handler for message recived for this Nep
        #we update the value of the variable
        msg=msg["content"]["data"]
        i = msg.index("/")
        msg_format_correct = (i != -1)
        if msg_format_correct:
            varname = msg[:i]
            if varname in self.vars_to_update:
                val_str = msg[i+1:]
                if self.var_types[varname] == "float":
                    varvalue = float(val_str)
                elif self.var_types[varname] == "int":
                    varvalue = int(val_str)
                elif self.var_types[varname] == "float_vec":
                    val_str = val_str[1:-1]
                    varvalue = tuple([float(x) for x in val_str.split(";")])
                elif self.var_types[varname] == "int_vec":
                    val_str = val_str[1:-1]
                    varvalue = tuple([int(x) for x in val_str.split(";")])
                elif self.var_types[varname] == "list":
                    varvalue = val_str.split("|")[:-1]
                else:
                    varvalue = val_str
                if not self.neos_updates_locked:
                    setattr(Variables,"_"+varname,varvalue)
                else:
                    self.var_temp_vals[varname] = varvalue
            else:
                print("Warning: Neos is trying to update variable "+varname+" that is not Nep's vars_to_update")
        else:
            print("Warning: Neos message type not supported (it doesn't have the format varname/varvalue)")

    def _send_var(self,var_name,var_value):
        var_type=type(var_value)
        value_str=""
        if var_type is str:
            value_str=var_value
        elif var_type is tuple:
            value_str="["+";"+join([str(x) for x in var_value])+"]"
        elif var_type is list:
            value_str="|"+join([str(x) for x in var_value])+"|"
        else:
            value_str=str(var_value)
        self.comm.send("updateVar/"+var_name+"/"+value_str)

    def send(self, var_name, custom_name=None, value=None):
        var_value = value
        #IDEA: Maybe put this functionality in another method. send_custom or something!
        if value is None:
            frame = inspect.currentframe()
            locals = frame.f_back.f_locals # local variables from calling scope
            var_value = locals[var_name]

        if custom_name is not None:
            var_name = custom_name
        self._send_var(var_name,var_value)

    def bind(self,varname,callback=None,type="float",update_neos=True,update_python=True):
        prop = property(fset=Variables._generate_set(varname,update_neos,callback),fget=lambda self: Variables.__dict__["_"+varname], fdel=Variables._generate_del(varname,update_neos))
        setattr(Variables,"_"+varname,None)
        setattr(Variables,varname,prop)
        self.comm.send("addVar/"+varname)
        if update_python:
            if varname not in self.vars_to_update:
                self.vars_to_update.append(varname)
                self.var_types[varname]=type

    def plot(self,plt):
        plt.plot()
        figname = "img/"+uuid.uuid1().hex+".png"
        plt.savefig(figname)
        self.comm.send("media/"+"http://localhost:8000/"+figname)


    def listen(self, varname):
        frame = inspect.currentframe()
        locals = frame.f_back.f_locals # local variables from calling scope
        #TODO: this one only upates the local variable when neos changes the variable

    def lock(self):
        #freeze updating of variables from Neos, and instead update to a temp storage of variables
        self.neos_updates_locked = True

    def unlock(self):
        #unfreeze the variables from Neos, and update them according to the stored updates
        self.neos_updates_locked = False
        for varname in self.var_temp_vals:
            setattr(Variables,"_"+varname,self.var_temp_vals[varname])
        self.var_temp_vals = {}

    def reactive_loop(self,function,iterable,*args,**kwargs):
        #TODO: iterate function with iterable, unlocking and locking the self.vars before every iteration.
        # run iteration in another thread to allow for neos to update the variables between each iteration
        def loop():
            for it in iterable:
                self.lock()
                function(it,*args,**kwargs)
                self.unlock()

        t = threading.Thread(target=loop)
        t.start()
        pass

#nep.read / user prompt. Implement with thejupyter api read-from-frontend stuff in Neos

class Variables(object):
    def __init__(self,comm,nep):
        self.comm = comm
        self.nep = nep

    @staticmethod
    def _generate_set(name,update_neos,callback):
        if update_neos:
            def set(self,value):
                setattr(Variables,"_"+name,value)
                self.nep._send_var(name,value)
                if callback is not None:
                    callback()
                #IDEA: could add here a thing that updates the nep.var_types according to the value set.
        else:
            def set(self,value):
                setattr(Variables,"_"+name,value)
                if callback is not None:
                    callback()
        return set

    @staticmethod
    def _generate_del(name,update_neos):
        if update_neos:
            def delete(self):
                del self.__class__.__dict__["_"+name]
                #TODO: add special message to indicate variable was deleted
        else:
            def delete(self):
                del self.__class__.__dict__["_"+name]
        return delete
