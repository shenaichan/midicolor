import time, threading

import rtmidi

from music21 import chord

from flask import Flask
from flask_socketio import SocketIO

################################################################

app = Flask(__name__)
app.config["SECRET_KEY"] = "foobar"

socketio = SocketIO(app, cors_allowed_origins="*")

################################################################

class ChordAnalyzer:
    def __init__(self):
        self.current_notes = set()
        self.lock = threading.Lock()
        self.midi_in = rtmidi.MidiIn()
    
    def _midi_to_color_idx(self, note):
        return (note * 7) % 12
    
    def midi_callback(self, data, _):
        msg, _ = data
        # print("MIDI message: ", msg)

        if len(msg) == 3:
            status, note, velocity = msg
            with self.lock:
                if status == 144 and velocity > 0:
                    self.current_notes.add(note)
                    color_idx = self._midi_to_color_idx(note)
                    socketio.emit("midiEvent", {"colorIdx": color_idx})

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
                color_idxs = [self._midi_to_color_idx(note) for note in self.current_notes]
                print(color_idxs)
                socketio.emit("chordEvent", {"notes": color_idxs, "name": chord})
            time.sleep(0.1)

################################################################

if __name__ == "__main__":
    analyzer = ChordAnalyzer()

    midi_thread = threading.Thread(target=analyzer.start_monitoring, daemon=True)
    midi_thread.start()

    socketio.run(app, host="localhost", port=8080, debug=True)

