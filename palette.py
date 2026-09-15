#!/usr/bin/env python3

import itertools

COLORS = [
    '#ff0000',
    '#00ff00',
    '#0000ff',
    '#ffff00',
    '#00ffff',
    '#ff00ff',
    '#aa0000',
    '#00aa00',
    '#0000aa',
    '#ffaa00',
    '#aa00ff',
    '#ffaa00',
    '#00ffaa',
    '#ff00aa',
    '#00aaff',
    '#aaff00',
    '#aa00aa',
    '#00aaaa',
    '#aaaa00',
]

def tikz_color(index):
    index = index%len(COLORS)
    return f'palettecolor{index+1}'

def tikz_palette():
    result = []
    for index, color in zip(itertools.count(), COLORS):
        r = str(int(color[1:3],16)/255)
        g = str(int(color[3:5],16)/255)
        b = str(int(color[5:7],16)/255)
        result.append('\\definecolor{'+tikz_color(index)+'}{rgb}{'+r+','+g+','+b+'}')
    return '\n'.join(result)
