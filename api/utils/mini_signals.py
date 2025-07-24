from typing import Callable

class Signal:
    def __init__(self, initial=None):
        self._value = initial
        self._listeners = []
        
    def connect(self, callback: Callable):
        self._listeners.append(callback)
        
    def set(self, value):
        self._value = value
        for callback in self._listeners:
            callback(value) # notify listeners
            
    def get(self):
        return self._value
    
class Signals:
    def __init__(self):
        self._signals = {}
        
    def create(self, name: str, initial=None):
        sig = Signal(initial)
        self._signals[name] = sig
        return sig

signals = Signals()
pdf_download_signal = signals.create("pdf_download_signal")