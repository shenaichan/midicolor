import time, threading

import rtmidi

from music21 import chord

################################################################
class ChordAnalyzer:
    def __init__(self):
        self.current_notes = set()
        self.lock = threading.Lock()
        self.midi_in = rtmidi.MidiIn()
    
    def midi_callback(self, data, _):
        msg, _ = data
        # print("MIDI message: ", msg)

        if len(msg) == 3:
            status, note, velocity = msg
            with self.lock:
                if status == 144 and velocity > 0:
                    self.current_notes.add(note)
                elif status == 128 or (status == 144 and velocity == 0):
                    self.current_notes.discard(note)
    
    def get_current_chord(self):
        with self.lock:
            c = chord.Chord(self.current_notes).pitchedCommonName
            if c != "empty chord":
                return c
    
    def start_monitoring(self):
        self.midi_in.set_callback(self.midi_callback)
        available_ports = self.midi_in.get_ports()
        if available_ports:
            self.midi_in.open_port(0)
            print(available_ports[0])
        else:
            print("No available MIDI ports :(")
            return
        
        while True:
            chord = self.get_current_chord()
            if chord:
                print(f"Current chord: {chord}")
            time.sleep(0.1)

if __name__ == "__main__":
    analyzer = ChordAnalyzer()
    analyzer.start_monitoring()