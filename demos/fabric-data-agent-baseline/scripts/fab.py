import json,os,subprocess,sys,urllib.request,urllib.error
def tok():
    return subprocess.run(['/home/box/tools/azcli/bin/az','account','get-access-token','--resource','https://api.fabric.microsoft.com','--query','accessToken','-o','tsv'],capture_output=True,text=True,check=True).stdout.strip()
T=None
def call(method,path,body=None):
    global T
    T=T or tok()
    url=path if path.startswith('http') else 'https://api.fabric.microsoft.com/v1'+path
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(url,data=data,method=method,headers={'Authorization':'Bearer '+T,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(r) as resp:
            txt=resp.read().decode(); return resp.status,(json.loads(txt) if txt else None),dict(resp.headers)
    except urllib.error.HTTPError as e:
        txt=e.read().decode()
        try: j=json.loads(txt)
        except: j=txt
        return e.code,j,dict(e.headers)
