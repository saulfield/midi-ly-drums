import midi


class Note:
    def __init__(self):
        self.pitch = None
        self.velocity = None
        self.start_ticks = None
        self.end_ticks = None
        self.length_ticks = None

    def __repr__(self):
        return "Note(pitch=%r, velocity=%r, start=%r, length=%r)" % \
               (self.pitch, self.velocity, self.start_ticks, self.length_ticks)

    def calc_length(self):
        self.length_ticks = self.end_ticks - self.start_ticks


def midi_to_notes(midi_file_name):
    pattern = midi.read_midifile(midi_file_name)
    resolution = pattern.resolution     # Ticks per measure
    track = pattern[0]
    tick = 0

    incomplete_notes = list()
    complete_notes = list()

    for i in range(len(track)):
        event = track[i]
        tick += event.tick
        if type(event) == midi.events.NoteOnEvent:
            note = Note()
            note.pitch = event.pitch
            note.velocity = event.velocity
            note.start_ticks = tick
            incomplete_notes.append(note)
        elif type(event) == midi.events.NoteOffEvent:
            for n in incomplete_notes:
                if n.pitch == event.pitch:
                    n.end_ticks = tick
                    n.calc_length()
                    complete_notes.append(n)
                    incomplete_notes[:] = [x for x in incomplete_notes if x is not n]
                    break
    return complete_notes


def main():
    notes = midi_to_notes('midi-files/onebeat.mid')
    print notes

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Exiting"
