#!/usr/bin/env python3

import copy
import itertools
import logging
import pathlib
import shutil
import subprocess
import tempfile
import yaml

from palette import tikz_color, tikz_palette

class ShortListDumper(yaml.SafeDumper):
    pass

def represent_list(dumper, data):
    node = dumper.represent_list(data)
    node.flow_style = True
    return node

ShortListDumper.add_representer(list, represent_list)
ShortListDumper.add_representer(tuple, represent_list)

def yaml_dump(data):
    return yaml.dump(data, Dumper=ShortListDumper, sort_keys=False, width=10**9)

def tikz_to_pdf(tikz, path):
    path = pathlib.Path(path).resolve()
    tex = []
    tex.append(f'\\documentclass[border=20pt]{{standalone}}')
    tex.append(f'\\usepackage{{tikz}}')
    tex.append(f'\\usetikzlibrary{{fit,backgrounds,patterns}}')
    tex.append(tikz_palette())
    tex.append(f'\\begin{{document}}')
    tex.append(f'\\begin{{tikzpicture}}[]')
    tex.append(tikz)
    tex.append(f'\\end{{tikzpicture}}')
    tex.append(f'\\end{{document}}')
    tex = '\n'.join(tex)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp).resolve()
        (tmp/'main.tex').write_text(tex)
        subprocess.run(['latexmk', '-silent', '-pdflatex', 'main'],
                       cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(tmp/'main.pdf', path)
        except:
            shutil.move(tmp/'main.tex', path)

        logging.debug(f'Succesfully created PDF `{path}`')

def tikz_to_svg(tikz, path):
    path = pathlib.Path(path).resolve()
    tex = []
    tex.append(f'\\documentclass[dvisvgm]{{minimal}}')
    tex.append(f'\\usepackage{{tikz}}')
    tex.append(f'\\usetikzlibrary{{fit,backgrounds,patterns}}')
    tex.append(tikz_palette())
    tex.append(f'\\begin{{document}}')
    tex.append(f'\\begin{{tikzpicture}}[]')
    tex.append(tikz)
    tex.append(f'\\end{{tikzpicture}}')
    tex.append(f'\\end{{document}}')
    tex = '\n'.join(tex)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp).resolve()
        (tmp/'main.tex').write_text(tex)
        subprocess.run(['latexmk', '-silent', '-dvi', 'main'],
                       cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.run(['dvisvgm', 'main'],
                       cwd=tmp)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(tmp/'main.svg', path)
        logging.debug(f'Succesfully created SVG `{path}`')


class Fence:

    balance_shift = 0

    def __init__(self, *, order=0, height=0, permutations=[]):
        self.order = int(order)
        self.height = int(height)
        self.permutations = tuple([ tuple([ int(elem) for elem in perm ]) for perm in permutations ])
        assert len(self.permutations) == self.height
        for perm in self.permutations:
            assert len(perm) == self.order
            for elem in perm:
                assert elem >= 1 and elem <= order
            assert len(set(perm)) == self.order

    @property
    def width(self):
        return self.order*(self.order+1)//2

    def get_permutation_partial_sums(self, index):
        raise NotImplementedError()

    @property
    def partial_sums(self):
        result = set()
        for index in range(self.height):
            result.update(set(self.get_permutation_partial_sums(index)))
        return tuple(sorted(list(result)))

    @property
    def balanced(self):
        for index in range(self.height):
            sums = self.get_permutation_partial_sums(index)
            reduced_sums = [ (s-self.balance_shift)//self.height for s in sums ]
            if len(reduced_sums) != len(set(reduced_sums)):
                return False
        return True


    @property
    def breakfree(self):
        result = set()
        for index in range(self.height):
            addition = set(self.get_permutation_partial_sums(index))
            before = len(result)
            result.update(addition)
            after = len(result)
            if after != before + len(addition):
                return False
        return True

    @property
    def tikz(self):
        return self.get_tikz()

    def get_tikz(self):
        raise NotImplementedError()

    @classmethod
    def from_data(cls, data):
        assert 'barrycade' in data or 'corral' in data
        if 'barrycade' in data:
            return cls.barrycade.from_data(data)
        elif 'corral' in data:
            return cls.corral.from_data(data)

    def to_data(self):
        raise NotImplementedError()

    @classmethod
    def from_path(cls, path):
        path = pathlib.Path(path).resolve()
        data = yaml.safe_load(path.read_text())
        return cls.from_data(data)

    def to_path(self, path):
        path = pathlib.Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml_dump(self.to_data()))

    def to_pdf(self, path):
        tikz_to_pdf(self.get_tikz(), path)

    def to_svg(self, path):
        tikz_to_svg(self.get_tikz(), path)

    def to_tex(self, path):
        path = pathlib.Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.get_tikz())

    def to_auto(self, path):
        if path == '-':
            print(yaml_dump(self.to_data()))
            return
        suffix = pathlib.Path(path).suffix.lower()
        if suffix == '.yaml':
            self.to_path(path)
        elif suffix == '.tex':
            self.to_tex(path)
        elif suffix == '.svg':
            self.to_svg(path)
        elif suffix == '.pdf':
            self.to_pdf(path)
        else:
            logging.error(f'Suffix {suffix} of output path is not recognized')
            raise NotImplementedError()


class Corral(Fence):

    def __init__(self, *, shifts=[], **kwargs):
        super().__init__(**kwargs)
        self.shifts = tuple([ int(shift) for shift in shifts ])
        assert len(self.shifts) == self.height

    def get_permutation_partial_sums(self, index):
        assert index >= 0 and index < self.height
        result = list()
        partial = self.shifts[index] % self.width
        for elem in self.permutations[index]:
            partial = (partial + elem) % self.width
            result.append(partial)
        return tuple(result)

    def get_tikz(self):
        result = []
        result.append('\\begin{scope}')
        for x in range(0,self.order*(self.order+1)//2+1):
            result.append(f'\\draw[dotted, draw=black] ({x},{self.height+0.25}) -- ({x},-0.25);')
            result.append(f'\\node[align=center, anchor=north] at ({x},-0.25) {{${x%self.width}$}};')
        for y in range(self.height):
            result.append(f'\\node[align=center, anchor=east] at (-0.25, {y+0.5}) {{$\\varrho_{{{y+1}}}:$}};')
            result.append(f'\\node[align=center, anchor=south] at ({self.shifts[y]},{self.height+0.25}) {{$\\tau_{{{y+1}}}$}};')
        result.append('\\begin{scope}')
        #result.append('\\clip (0,0) rectangle ({self.width},{self.height});')
        result.append(f'\\clip (-0.25,-0.25) rectangle ({self.width+0.25},{self.height+1.25});')
        for y, perm, shift in zip(itertools.count(), self.permutations, self.shifts):
            x = shift%self.width
            for elem in perm:
                x1 = x
                x2 = x + elem
                y1 = y
                y2 = y + 1
                color = tikz_color(elem)
                result.append(f'\\node[align=center, fill=white] at ({(x1+x2)/2}, {(y1+y2)/2}) {{${elem}$}};') 
                result.append(f'\\draw[fill={color}, fill opacity=0.5, draw=black, thick] ({x1}, {y1}) rectangle ({x2}, {y2});') 
                result.append(f'\\node[align=center] at ({(x1+x2)/2}, {(y1+y2)/2}) {{${elem}$}};') 
                x = (x+elem)%self.width
                if x < x1:
                    x2=x
                    x1=x-elem
                    result.append(f'\\node[align=center, fill=white] at ({(x1+x2)/2}, {(y1+y2)/2}) {{${elem}$}};') 
                    result.append(f'\\draw[fill={color}, fill opacity=0.5, draw=black, thick] ({x1}, {y1}) rectangle ({x2}, {y2});') 
                    result.append(f'\\node[align=center] at ({(x1+x2)/2}, {(y1+y2)/2}) {{${elem}$}};') 
                    #result.append(f'\\fill[pattern=crosshatch, pattern color={color}, fill opacity=0.5] (0, {y1}) rectangle ({x}, {y2});') 
                    #result.append(f'\\draw[draw=black, thick] (0, {y1}) -- ({x}, {y1}) -- ({x}, {y2}) -- (0, {y2});') 
                if x1 == 0:
                    x1=self.width
                    x2=x1+elem
                    result.append(f'\\node[align=center, fill=white] at ({(x1+x2)/2}, {(y1+y2)/2}) {{${elem}$}};') 
                    result.append(f'\\draw[fill={color}, fill opacity=0.5, draw=black, thick] ({x1}, {y1}) rectangle ({x2}, {y2});') 
                    result.append(f'\\node[align=center] at ({(x1+x2)/2}, {(y1+y2)/2}) {{${elem}$}};') 
        result.append('\\end{scope}')
        result.append('\\end{scope}')
        result = '\n'.join(result)
        return result

    @classmethod
    def from_data(cls, data):
        assert 'corral' in data
        corral = data['corral']
        order = corral['order']
        height = corral['height']
        permutations = corral['permutations']
        shifts = corral['shifts']
        return Corral(order=order, height=height, permutations=permutations, shifts=shifts)

    def to_data(self):
        corral = dict()
        corral['order'] = self.order
        corral['height'] = self.height
        corral['permutations'] = self.permutations
        corral['shifts'] = self.shifts
        data = dict()
        data['corral'] = corral
        return copy.deepcopy(data)

Fence.corral = Corral


class Barrycade(Fence):
    balance_shift = 1
    def get_permutation_partial_sums(self, index):
        assert index >= 0 and index < self.height
        result = list()
        partial = 0
        for elem in self.permutations[index]:
            partial += elem
            result.append(partial)
        return tuple(result[:-1])

    def get_tikz(self):
        result = []
        result.append('\\begin{scope}')
        for x in range(1,self.order*(self.order+1)//2):
            result.append(f'\\draw[dotted, draw=black, draw opacity=0.5] ({x},{self.height+0.25}) -- ({x},-0.25);')
            result.append(f'\\node[align=center, anchor=north] at ({x},-0.25) {{${x}$}};')
        for y, perm in zip(itertools.count(), self.permutations):
            result.append(f'\\node[align=center, anchor=east] at (-0.25, {y+0.5}) {{$\\varrho_{{{y+1}}}:$}};')
            x = 0
            for elem in perm:
                x1 = x
                x2 = x + elem
                y1 = y
                y2 = y + 1
                color = tikz_color(elem)
                result.append(f'\\node[align=center, fill=white] at ({(x1+x2)/2}, {(y1+y2)/2}) {{${elem}$}};') 
                result.append(f'\\draw[fill={color},fill opacity=0.5, draw=black, draw opacity=1, thick] ({x1}, {y1}) rectangle ({x2}, {y2});') 
                result.append(f'\\node[align=center] at ({(x1+x2)/2}, {(y1+y2)/2}) {{${elem}$}};') 
                x += elem
        result.append('\\end{scope}')
        result = '\n'.join(result)
        return result

    @classmethod
    def from_data(cls, data):
        assert 'barrycade' in data
        barrycade = data['barrycade']
        order = barrycade['order']
        height = barrycade['height']
        permutations = barrycade['permutations']
        return Barrycade(order=order, height=height, permutations=permutations)

    def to_data(self):
        barrycade = dict()
        barrycade['order'] = self.order
        barrycade['height'] = self.height
        barrycade['permutations'] = self.permutations
        data = dict()
        data['barrycade'] = barrycade
        return copy.deepcopy(data)

Fence.barrycade = Barrycade
