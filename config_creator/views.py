from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .modules.runner import Runner
from .settings import *
import os, tempfile

def index(request):
    template = loader.get_template('config_creator/index.html')
    context = {}
    response = HttpResponse(template.render(context, request))
    return response

def generate(request, template):
    username = 'admin'
    password = 'admin'
    identity = 'Switch0'
    fd, outfile = tempfile.mkstemp(suffix='.rsc')
    os.close(fd)
    uplink = 'ether1'
    vlans = {
        1034: [('ether','2'),('ether','3')]
    }

    runner = Runner(['python3', os.path.join(GENCONFIG_DIR,'genconfig.py')])
    runner.start()
    runner.write(template)
    runner.write(username)
    runner.write(password)
    runner.write(identity)
    runner.write(outfile)
    runner.write(uplink)

    line = runner.read()
    while runner.process.poll() is None:
        if line.startswith('Setting up VLAN'):
            vid = int(line[16:])
        elif line.startswith('available VLANs with this VID:'):
            runner.write('1')
        elif line.startswith("WARNING: Couldn't fetch VLAN info from NetBox"):
            runner.write('y')
            runner.write(f'vlan{vid}')
        elif line.startswith("which ports have this VLAN as primary?"):
            if vid in vlans:
                for port in vlans[vid]:
                    runner.write(port[0]+' '+port[1])
                vlans.pop(vid)
            runner.write('.')
        elif line.startswith("Type [V] to add a VLAN or [E] to save changes:"):
            if vlans:
                runner.write('V')
            else:
                runner.write('E')
        elif line.startswith('vid:'):
            for i in vlans:
                vid = i
                break
            runner.write(str(vid))
        elif line.startswith('ERROR'):
            runner.terminate()
            return HttpResponse(line)
        line = runner.read()

    with open(outfile) as fd:
        result = fd.read()
    os.remove(outfile)
    return HttpResponse(result, headers={
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename="config.rsc"',
    })
