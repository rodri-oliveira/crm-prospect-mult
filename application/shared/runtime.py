"""Avoid starting another CRM process on an already occupied port."""
import socket


def port_in_use(host, port):
    probe = '127.0.0.1' if host in ('0.0.0.0', '::') else host
    try:
        with socket.create_connection((probe, port), timeout=0.3):
            return True
    except OSError:
        return False
