from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .modules.runner import Runner
from .settings import *
import os, tempfile
import json

VERSION = '1.01' # compatible with genconfig v1.03
TEMPLATE_DIR = os.path.join(GENCONFIG_DIR,'templates')

def index(request):
    htmlTemplate = loader.get_template('config_creator/index.html')
    templates = []
    for t in os.listdir(TEMPLATE_DIR):
        if t.endswith(".rsc.template"):
            templates.append(t[:-13])
    templates.sort()
    context = {
        'templates': templates,
        'version': VERSION,
    }
    response = HttpResponse(htmlTemplate.render(context, request))
    return response

def genform(request, template):
    htmlTemplate = loader.get_template('config_creator/genform.html')
    with open(os.path.join(TEMPLATE_DIR,template+'.json')) as tjson:
        device = json.loads(tjson.read())
    context = {
        'template': template,
        'version': VERSION,
        'interfaces': device["interfaces"],
    }
    response = HttpResponse(htmlTemplate.render(context, request))
    return response

def generate(request, template):
    username = request.GET['username'].replace('\n',' ')
    password = request.GET['password'].replace('\n',' ')
    identity = request.GET['identity'].replace('\n',' ')
    fd, outfile = tempfile.mkstemp(suffix='.rsc')
    os.close(fd)
    uplink = request.GET['uplink'].replace('\n',' ')
    vlans = {}
    for entry in request.GET:
        print(entry,':',request.GET[entry])
        if entry.endswith('-role') and request.GET[entry] == 'vlan':
            pname = entry[:-5]
            if pname.startswith('ether'):
                ptype = 'ether'
                pnum = pname[5:]
            elif pname.startswith('sfpp'):
                ptype = 'sfpp'
                pnum = pname[4:]
            else:
                continue
            vid = int(request.GET[f'{pname}-vlanid'])
            if vid not in vlans:
                vlans[vid] = [(ptype,pnum)]
            else:
                vlans[vid].append((ptype,pnum))

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
