from neptune import Nep
from multiprocessing import Process
import subprocess
from neptune.mwserver import start_kernel,set_up_nep
# from IPython.kernel.comm import manager
from ipykernel.comm import Comm
from ipykernel.ipkernel import Kernel
import time
if __name__ == "__main__":
    auth_token = ""
    base='http://localhost:8888'
    # # server_process = Process(target=start_kernel, args=(auth_token),daemon=True)
    # # server_process.start()
    kernel_config = start_kernel(base,auth_token)
    time.sleep(1)
    set_up_nep(kernel_config["id"],auth_token,8766)
    # kernel = Kernel(**kernel_config)
    # self.comm = Comm(target_name="neos_comm")
    # self.comm.open()
    # def func(comm,msg):
    #     # comm is the frontend comm instance
    #     # msg is the comm_open message, which can carry data
    #
    #     # Register handlers for later messages:
    #     # comm.on_msg(function(msg) {...});
    #     # comm.on_close(function(msg) {...});
    #     # comm.send({'foo': 0});
    #     print(comm)
    # manager.CommManager.register_target('my_comm_target',func)
    # nep = Nep()
    # nep.start()


# from IPython.kernel.comm import manager
# from IPython.kernel.connect import ConnectionFileMixin

# import IPython
#
# IPython.start_kernel()
