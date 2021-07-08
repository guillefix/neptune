Hi Neptune is a NeosVR frontend for Jupyter kernels. 

I really should write some more in here

Demo: https://www.youtube.com/watch?v=W2_1HyXo18Y&ab_channel=GuillermoValle

Another demo: https://twitter.com/guillefix/status/1326687429726769154

Run jupyter as `jupyter notebook --NotebookApp.allow_origin="*" --NotebookApp.token="" --NotebookApp.disable_check_xsrf=True`


or `jupyter kernel --ip='*' --f=./remotekernel.json` for a standalone kernel, to be used with BlockingKernelClient as in app2.py, but then the websocket api is not available... and need to use the KernelClient API.... Actually no, I think it was `start_kernel.py` that worked...

<img src="https://user-images.githubusercontent.com/7515537/124844812-8df99f80-df95-11eb-87d1-bfdd4e0f2142.png" data-canonical-src="https://gyazo.com/eb5c5741b6a9a16c692170a41a49c858.png" width="200" height="180" />
