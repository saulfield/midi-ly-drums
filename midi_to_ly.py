#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Takes a MIDI file as input, creates a LilyPond score out of it, and outputs it as a PDF.
"""

import midi
import os
import subprocess


QUARTER = 1
EIGHTH = 2
SIXTEENTH = 4

NOTE_TYPES = [QUARTER, EIGHTH, SIXTEENTH]
TYPE_TO_LY = {QUARTER: 4, EIGHTH: 8, SIXTEENTH: 16}
# Mapping of MIDI pitch to LilyPond string, based on General Midi Percussion Standard
NOTE_PITCHES = {36: 'bd', 38: 'sn', 42: 'hh'}


class NoteGroup:
    def __init__(self, note=None):
        self.notes = list()
        self.note_type = None
        if note is not None:
            self.notes.append(note)
            self.start_ticks = note.start_ticks

    # TODO: Make this more robust
    def set_note_type(self, resolution):
        lengths = [l.length_ticks for l in self.notes]
        m = max(lengths)
        t = int(resolution/m)
        if t not in NOTE_TYPES:
            print "Note type not found"
            return
        else:
            self.note_type = t
            return


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


def midi_to_notes(pattern):
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


def create_note_groups(notes):
    groups = list()
    group = NoteGroup()
    tick = -1   # Make sure the first group is created
    for n in notes:
        if n.start_ticks == tick:
            group.notes.append(n)
        else:
            tick = n.start_ticks
            group = NoteGroup(n)
            groups.append(group)
    return groups


def note_groups_to_ly(groups):
    ly_string = ''
    for g in groups:
        ly_note = ''
        for n in g.notes:                           # TODO: Add parenthesis based on velocity (ghost note)
            ly_note += ' ' + NOTE_PITCHES[n.pitch]
        ly_note = ly_note[1:]   # Remove first space
        if len(g.notes) > 1:
            ly_note = '<{0}>'.format(ly_note)
        ly_note += str(TYPE_TO_LY[g.note_type])
        ly_note += ' '                              # TODO: Add newline if end of measure
        ly_string += ly_note
    return ly_string


def construct_ly_string(ly_notes):
    ly = ''
    ly += '\\version "2.18.2"\n'     # TODO: Pass in lilypond version
    ly += '''
\\new DrumStaff {
    \\drummode { 
    
    \\numericTimeSignature 
    \\override Stem #'direction = #up\n
    '''
    ly += ly_notes
    ly += '''
    }
}
    '''
    return ly


def to_pdf(title, ly_string):
    """ Requires LilyPond added to PATH."""
    c = 'lilypond -fpdf -o "%s" "%s.ly"'
    try:
        f = open(title + '.ly', 'w')
        f.write(ly_string)
        f.close()
    except:
        return False
    c = 'lilypond -fpdf -o "{0}" "{1}.ly"'.format(title, title)
    print 'Executing: ' + c
    p = subprocess.Popen(c, shell=True).wait()
    # os.remove(title + '.ly')
    return True


def main():
    # Read MIDI file and save note data
    pattern = midi.read_midifile('midi-files/onebar.mid')  # TODO: Parse command line arguments
    resolution = pattern.resolution  # Ticks per quarter note
    notes = midi_to_notes(pattern)

    # Sort notes into groups
    groups = create_note_groups(notes)
    for g in groups:
        g.set_note_type(resolution)

    # Convert note data to lilypond notes
    ly_notes = note_groups_to_ly(groups)

    # Construct full ly file
    ly_string = construct_ly_string(ly_notes)

    # Output to pdf
    to_pdf('onebar', ly_string)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Exiting"
