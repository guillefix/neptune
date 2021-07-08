Hi Neptune is a NeosVR frontend for Jupyter kernels. 

I really should write some more in here

Demo: https://www.youtube.com/watch?v=W2_1HyXo18Y&ab_channel=GuillermoValle

Another demo: https://twitter.com/guillefix/status/1326687429726769154

Run jupyter as `jupyter notebook --NotebookApp.allow_origin="*" --NotebookApp.token="" --NotebookApp.disable_check_xsrf=True`


or `jupyter kernel --ip='*' --f=./remotekernel.json` for a standalone kernel, to be used with BlockingKernelClient as in app2.py, but then the websocket api is not available... and need to use the KernelClient API....
