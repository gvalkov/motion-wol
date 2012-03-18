#!/usr/bin/env python3
# encoding: utf-8

import asyncore
import traceback
import os, atexit

from sys import argv, exit
from time import time as utime
from os.path import abspath, exists
from functools import partial
from subprocess import Popen, PIPE, STDOUT, call

from motionwol import state
from motionwol.dsl import *


usage = 'usage: motionwol <named pipe> <config file> [<xmlrpc addr:port>]'


class FDDispatcher(asyncore.file_dispatcher):
    def writable(self):
        return False

    def handle_error(self):
        traceback.print_exc()

class FifoDispatch(FDDispatcher):
    def handle_read(self):
        self.recv(1024)
        now = int(utime())

        if not (state.last_motion[0] and state.prev_motion[0]):
            state.last_motion[0] = now

        state.prev_motion[0] = state.last_motion[0]
        state.last_motion[0] = now

        print('motion event at {}'.format(state.last_motion[0]))

        for rule in (i for i in state.config if i.enabled):
            if rule.eval():
                print('wake host {} up'.format(rule.host))
                wakeup(rule.host)

class PingDispatch(FDDispatcher):
    def handle_read(self):
        s = str( self.recv(1024) )
        if ' bytes from ' in s:
            state.pinglog[self.host] = int(utime())

class XmlRpcDispatch(FDDispatcher):
    def handle_read(self):
        self.server.handle_request()

def wakeup(host):
    call(('wakeonlan', host.mac))

def start_pings(interval=5):
    for rule in state.config:
        cmd = ('ping', '-i', str(interval), rule.host.addr)
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        PingDispatch(p.stdout).host = rule.host

def start_xmlrpc(bindaddr):
    from xmlrpc.server import (SimpleXMLRPCServer,
                               SimpleXMLRPCRequestHandler)

    class handler(SimpleXMLRPCRequestHandler):
        rpc_paths = ('/motionwol',)

    addr, port = bindaddr.split(':') #long live IPv4
    server = SimpleXMLRPCServer((addr, int(port)), allow_none=True, requestHandler=handler)
    server.register_introspection_functions()
    server.register_function(disable_rules, 'disable')
    server.register_function(enable_rules, 'enable')

    XmlRpcDispatch(server.fileno()).server = server

def disable_rules():
    for i in config: i.enabled = False

def enable_rules():
    for i in config: i.enabled = True

def cleanup(fifo_fn):
    print('clean up and exit')
    if exists(fifo_fn):
        os.unlink(fifo_fn)

def parseopt():
    try:
        fifo, config_fn = argv[1:3]
    except:
        print(usage)
        exit(1)

    try:    xmlrpc_bind = argv[3]
    except: xmlrpc_bind = None

    return abspath(fifo), abspath(config_fn), xmlrpc_bind

def main():
    fifo_fn, config_fn, xmlrpc_bind = parseopt()
    atexit.register(partial(cleanup, fifo_fn))

    print('create input fifo {}'.format(fifo_fn))
    os.mkfifo(fifo_fn)

    print('import config file {}'.format(config_fn))
    exec(open(config_fn).read()) # simply instantiating a rule adds it to state.config

    fifo_fd = os.open(fifo_fn, os.O_RDWR)
    FifoDispatch(fifo_fd)

    addrs = (i.host.addr for i in state.config)
    print('monitor hosts for inactivity: {}'.format(' '.join(addrs)))
    start_pings()

    if xmlrpc_bind:
        print('start xmlrpc control server on {}'.format(xmlrpc_bind))
        start_xmlrpc(xmlrpc_bind)

    asyncore.loop()

if __name__ == '__main__':
    main()
