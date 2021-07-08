from jupyter_core.application import JupyterApp, base_flags, base_aliases
from jupyter_client.consoleapp import (
        JupyterConsoleApp, app_aliases, app_flags,
    )
# from ipykernel.comm import Comm
from neptune.comms import Comm, CommManager
from neptune import Nep
import sys
import asyncio

class Neptune(JupyterApp,JupyterConsoleApp):
    name="neptune"
    description="nep nep"

    def _init_asyncio_patch(self):
        """
        Same workaround fix as https://github.com/ipython/ipykernel/pull/456
        Set default asyncio policy to be compatible with tornado
        Tornado 6 (at least) is not compatible with the default
        asyncio implementation on Windows
        Pick the older SelectorEventLoopPolicy on Windows
        if the known-incompatible default policy is in use.
        do this as early as possible to make it a low priority and overrideable
        ref: https://github.com/tornadoweb/tornado/issues/2608
        FIXME: if/when tornado supports the defaults in asyncio,
               remove and bump tornado requirement for py38
        """
        if sys.platform.startswith("win") and sys.version_info >= (3, 8):
            import asyncio
            try:
                from asyncio import (
                    WindowsProactorEventLoopPolicy,
                    WindowsSelectorEventLoopPolicy,
                )
            except ImportError:
                pass
                # not affected
            else:
                if type(asyncio.get_event_loop_policy()) is WindowsProactorEventLoopPolicy:
                    # WindowsProactorEventLoopPolicy is not compatible with tornado 6
                    # fallback to the pre-3.8 default of Selector
                    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    def _dispatch(self, msg):
        """Dispatch messages"""
        msg_type = msg['header']['msg_type']
        handled_msg_types = ['comm_open', 'comm_msg', 'comm_close']
        if msg_type in handled_msg_types:
            getattr(self, msg_type)(msg)

    def register_comm(self, comm):
        """Register a new comm"""
        comm_id = comm.comm_id
        comm.kernel_client = self.kernel_client
        self.comms[comm_id] = comm
        # comm.sig_is_closing.connect(self.unregister_comm)
        return comm_id

    def nep_start(self,comm):
        # self.register_comm(self.comm)
        # self.comm.open()
        # nep = Nep(comm)
        # nep.start()
        nep = Nep(comm,kernel_id=self.kernel_client.kernel_info())
        nep.start()

    def initialize(self,argv=None):
        JupyterConsoleApp.initialize(self,argv)
        kernel_manager = self.kernel_manager_class(
                                connection_file=self._new_connection_file(),
                                parent=self,
                                autorestart=True,
        )
        # start the kernel
        kwargs = {}
        self.comms = {}
        # FIXME: remove special treatment of IPython kernels
        if self.kernel_manager.ipykernel:
            kwargs['extra_arguments'] = self.kernel_argv
        # kernel_manager.start_kernel(**kwargs)
        kernel_manager.start_kernel()
        # kernel_manager.client_factory = self.kernel_client_class
        self.kernel_client = kernel_manager.client()
        self.kernel_client.start_channels(shell=True, iopub=True)
        # print(dir(self.kernel_client.shell_channel))
        self.comm_manager = CommManager(parent=self.kernel_client, kernel_client=self.kernel_client)
        # self.blocking_client = self.kernel_client.blocking_client()
        # self.blocking_client.start_channels(shell=True, iopub=True)
        # self.comm_manager = self.kernel_client.comm_manager
        # print(self.kernel_client)
        # kernel_client.start_channels(shell=True, iopub=True)
        # self._init_asyncio_patch()
        super().initialize(argv)
        # self.comm_manager = self.kernel_client.comm_manager
        # self.comm_manager.register_target('neos_comm', self.comm_open)
        comm = self.comm_manager.new_comm("neos_comm")
        self.nep_start(comm)
        # self.comm = Comm(target_name="neos_comm", kernel_client=self.kernel_client)
        # nep = Nep(self.comm,kernel_id=self.kernel_client.kernel_info())
        # nep.start()
        # self.comm_open(self.comm)
        # kernel_client.execute("nep=Nep()")
        # kernel_client.execute("nep.start()")
        # kernel_client.execute("1+1")
        # kernel_client.iopub_channel.message_received.connect(self._dispatch)

def main():
    # Neptune.launch_instance()
    from ipykernel.kernelapp import IPKernelApp
    app = IPKernelApp.instance()
    app.init_pdb()
    app.init_blackhole()
    app.init_connection_file()
    app.init_poller()
    app.init_sockets()
    app.init_heartbeat()
    # writing/displaying connection info must be *after* init_sockets/heartbeat
    app.write_connection_file()
    # Log connection info after writing connection file, so that the connection
    # file is definitely available at the time someone reads the log.
    app.log_connection_info()
    app.init_io()
    try:
        app.init_signal()
    except:
        # Catch exception when initializing signal fails, eg when running the
        # kernel on a separate thread
        if app.log_level < logging.CRITICAL:
            app.log.error("Unable to initialize signal:", exc_info=True)
    app.init_kernel()
    print(app.kernel)
    # app.initialize()
    # print("HII")
    # print(app.kernel)
    # app.start()

    # await asyncio.sleep(20)
    # print(nep)
    # await asyncio.sleep(5)
    # await nep.kernel_client._async_get_stdin_msg()

if __name__ == '__main__':
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # asyncio.run(main())
    main()
