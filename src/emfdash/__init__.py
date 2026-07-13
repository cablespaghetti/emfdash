#!/usr/bin/env python3
"""EMF Camp Dashboard - TUI dashboard for MQTT feeds."""

from .app import EmfDashApp

def main():
    app = EmfDashApp()
    app.run()
