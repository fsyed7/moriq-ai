"""Fixed deterministic subprocess fixtures. No live transport, tools or user code."""

import json
import logging
import os
import socket
import sys
import time
import urllib.request


def no_network(*args, **kwargs):
    raise RuntimeError('Network disabled')


socket.socket = no_network
socket.create_connection = no_network
urllib.request.urlopen = no_network


def fault_output(scenario, reply):
    if scenario == 'crash':
        os.write(2, b'PRIVATE_CRASH_PATH')
        os._exit(7)
    elif scenario == 'exception':
        raise RuntimeError('PRIVATE_EXCEPTION')
    elif scenario == 'noise':
        print('PRIVATE_PRINT', flush=True)
        logging.error('PRIVATE_LOG')
        os.write(1, b'PRIVATE_NATIVE_OUT')
        os.write(2, b'PRIVATE_NATIVE_ERR')
    elif scenario == 'stderr':
        os.write(2, b'PRIVATE_STDERR')
    elif scenario in {'large_stdout', 'large_stderr'}:
        os.write(1 if scenario == 'large_stdout' else 2, b'X' * 131072)
    elif scenario == 'raw':
        os.write(1, reply.encode('utf-8'))
        return True
    elif scenario == 'partial':
        os.write(1, b'{"text":"PRIVATE_PARTIAL')
        return True
    elif scenario == 'partial_error':
        os.write(1, b'{"text":"PRIVATE_PARTIAL')
        raise RuntimeError('PRIVATE_AFTER_PARTIAL')
    return False


def verify_network_guards():
    for call in (socket.socket, socket.create_connection, urllib.request.urlopen):
        try:
            call('forbidden')
        except RuntimeError:
            pass
        else:
            raise RuntimeError('Guard failure')


def main():
    data = json.loads(sys.stdin.buffer.read(65537))
    scenario = data['scenario']
    reply = data['reply']
    response = json.dumps({'done': True, 'text': reply})
    if fault_output(scenario, reply):
        return
    if scenario == 'block':
        time.sleep(60)
    elif scenario == 'slow':
        while True:
            os.write(1, b' ')
            time.sleep(0.03)
    elif scenario == 'delayed':
        time.sleep(0.3)
    elif scenario == 'network_guard':
        verify_network_guards()
    elif scenario == 'environment':
        # Return only whether the child inherited unexpected configuration, never its values.
        allowed = {'SYSTEMROOT', 'WINDIR', 'LC_CTYPE'}
        if set(os.environ) - allowed or set(data) != {'scenario', 'reply', 'request'}:
            raise RuntimeError('Unexpected worker configuration')
    elif scenario not in {'success', 'noise', 'stderr', 'large_stdout', 'large_stderr'}:
        raise ValueError('Unknown mock fixture')
    os.write(1, response.encode('utf-8'))


if __name__ == '__main__':
    main()
