#!/usr/bin/env python3
"""
Convenience entry point for Speech Synthesis Realism & Roboticness Audio Analyzer.
Delegates to tools/analyze_speech.py.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from tools.analyze_speech import main

if __name__ == "__main__":
    main()
