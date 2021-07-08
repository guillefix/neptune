import os
import sys
import time
import json

from contextlib import contextmanager
from subprocess import Popen, PIPE
from flaky import flaky

from jupyter_client import BlockingKernelClient
from jupyter_core import paths
from ipython_genutils import py3compat

from neptune.comms import Comm, CommManager
from neptune import Nep

SETUP_TIMEOUT = 60
TIMEOUT = 15


@contextmanager
def setup_kernel(cmd):
    """start an embedded kernel in a subprocess, and wait for it to be ready
    Returns
    -------
    kernel_manager: connected KernelManager instance
    """

    def connection_file_ready(connection_file):
        """Check if connection_file is a readable json file."""
        if not os.path.exists(connection_file):
            return False
        try:
            with open(connection_file) as f:
                json.load(f)
            return True
        except ValueError:
            return False

    kernel = Popen([sys.executable, '-c', cmd], stdout=PIPE, stderr=PIPE)
    try:
        # connection_file = os.path.join(
        #     paths.jupyter_runtime_dir(),
        #     'kernel-%i.json' % kernel.pid,
        # )
        connection_file = "./remotekernel2.json"
        # # wait for connection file to exist, timeout after 5s
        # tic = time.time()
        # while not connection_file_ready(connection_file) \
        #     and kernel.poll() is None \
        #     and time.time() < tic + SETUP_TIMEOUT:
        #     time.sleep(0.1)
        #
        # # Wait 100ms for the writing to finish
        # time.sleep(0.1)
        #
        # if kernel.poll() is not None:
        #     o,e = kernel.communicate()
        #     e = py3compat.cast_unicode(e)
        #     raise IOError("Kernel failed to start:\n%s" % e)
        #
        # if not os.path.exists(connection_file):
        #     if kernel.poll() is None:
        #         kernel.terminate()
        #     raise IOError("Connection file %r never arrived" % connection_file)

        client = BlockingKernelClient(connection_file=connection_file)
        client.load_connection_file()
        # client.start_channels()
        # client.wait_for_ready()
        # client.
        comm_manager = CommManager(parent=client, kernel_client=client)
        comm = comm_manager.new_comm("neos_comm")
        # comm.open()
        nep = Nep(comm,kernel_id=client.kernel_info())
        nep.start()
        # self.nep_start(comm)
        # print(client.)
        try:
            yield client
        finally:
            # client.stop_channels()
            pass
    finally:
        # kernel.terminate()
        pass


def run():
    """IPython.embed_kernel() is basically functional"""
    cmd = '\n'.join([
        'from IPython import embed_kernel',
        'def go():',
        '    a=5',
        '    b="hi there"',
        '    embed_kernel()',
        'go()',
        '',
    ])

    with setup_kernel(cmd) as client:
        time.sleep(100)
        # oinfo a (int)
        # msg_id = client.inspect('a')
        # msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
        # content = msg['content']
        # assert content['found']
        #
        # msg_id = client.execute("c=a*2")
        # msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
        # content = msg['content']
        # assert content['status'] == 'ok'
        #
        # # oinfo c (should be 10)
        # msg_id = client.inspect('c')
        # msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
        # content = msg['content']
        # assert content['found']
        # text = content['data']['text/plain']
        # assert '10' in text

if __name__ == "__main__":
    run()
