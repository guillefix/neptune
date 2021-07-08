



Run jupyter as `jupyter notebook --NotebookApp.allow_origin="*" --NotebookApp.token="" --NotebookApp.disable_check_xsrf=True`


or `jupyter kernel --ip='*' --f=./remotekernel.json` for a standalone kernel, to be used with BlockingKernelClient as in app2.py, but then the websocket api is not available... and need to use the KernelClient API....
