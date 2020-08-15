import html
import textwrap
import pathlib
from abc import ABC


def indent(text, amount, ch=' '):
    return textwrap.indent(text, amount * ch)


class Base(ABC):
    def check(self):
        raise NotImplementedError


class Answer(Base):
    def __init__(self, name, is_correct):
        self.text = name.strip()
        self.is_correct = is_correct

        self.html_escaped = '<p>{}</p>'.format(html.escape(self.text, False))
        self.html = '<p>{}</p>'.format(self.text)

        if self.is_correct:
            to_add = '<input type="hidden" id="Corretta">'
            self.html_escaped = to_add + self.html_escaped
            self.html = to_add + self.html

    def check(self):
        assert self.text, 'Found empty text for answer!'

    def __str__(self):
        return 'RISPOSTA{e}: {r}'.format(e=' ESATTA' if self.is_correct else '', r=self.text)


class Question(Base):
    def __init__(self, number, global_number, name, module):
        self.name = name.strip()
        self.number = number
        self.global_number = global_number
        self.answers = []
        self.module = module
        self.jump2slides = None
        self.jump2slide = None

    def set_jump2slides(self, j2s):
        self.jump2slides = j2s
        self.jump2slide = min(j2s)

    def add_answer(self, answer):
        self.answers.append(answer)

    def check(self):
        where = 'uf: {u}, module: {m}, question: {q} / global question: {gq}'.format(
            u=self.module.unity.number + 1,
            m=self.module.number + 1,
            q=self.number + 1,
            gq=self.global_number + 1
        )
        assert self.answers, 'No answer found. [{}]'.format(where)

        count_correct = sum(1 for ans in self.answers if ans.is_correct)
        assert count_correct > 0, 'No correct answer found. [{}]'.format(where)
        assert count_correct == 1, 'More than one correct answer found. [{}]'.format(where)

        assert self.jump2slide, 'No slide to jump in case of error. [{}]'.format(where)

        for ans in self.answers:
            try:
                ans.check()
            except AssertionError as e:
                raise AssertionError(str(e) + ' [{}]'.format(where))

    def __str__(self):
        return self.str()

    def str(self, **kwargs):
        ordered = kwargs.get('ordered', True)
        indent_amount = kwargs.get('indent', 4)
        assert indent_amount >= 0

        answers = sorted(self.answers, key=lambda ans: not ans.is_correct) if ordered else self.answers
        correct_answer = [ans for ans in answers if ans.is_correct][0]

        s = 'DOMANDA {n} [{gn}]: {t}\n'.format(n=self.number + 1, gn=self.global_number + 1, t=self.name)
        s += '\n'.join([str(ans) for ans in answers])
        s += '\nHTML CORRETTA: {}'.format(correct_answer.html)
        s += '\nSE ERRORE, SALTA A {}'.format(self.jump2slide)
        # stampa tutte le slides a cui saltare, se sono più di una
        s += '{}'.format(' ' + str(self.jump2slides) if len(self.jump2slides) > 1 else '')

        return indent(s, indent_amount)


class Module(Base):
    def __init__(self, number, name, duration, unity):
        self.name = name.replace('/', ' e ').strip()
        self.number = number
        self.duration = duration
        self.questions = []
        self.questions_sorted = []
        self.unity = unity

    def add_question(self, question):
        self.questions.append(question)
        self.questions_sorted.append(question)

    def sort_questions(self):
        assert all(q.jump2slide is not None for q in self.questions), \
            'There are still questions without the slide to jump yet!'
        self.questions_sorted.sort(key=lambda q: q.jump2slide)

    def check(self):
        assert self.questions, 'No question found for module {}'.format(self.name)

        for question in self.questions:
            question.check()

    def __str__(self):
        return self.str(ordered=False, separated=False)

    def str(self, **kwargs):
        ordered = kwargs.get('ordered', True)
        separated = kwargs.get('separated', False)
        indent_amount = kwargs.get('indent', 4)
        assert indent_amount >= 0

        s = 'MODULO {n}: {t} - Durata {h} Ore\n'.format(n=self.number + 1, t=self.name, h=self.duration)
        s += 'DOMANDE (NUMERO): {}\n'.format(len(self.questions))
        # cambiando l'array, cambia l'ordine della stampa delle domande
        qs = self.questions_sorted if ordered else self.questions
        to_print = [str(q) for q in qs]
        if separated:
            candidates = [x for x in range(4, 7) if len(to_print) % x == 0] or [5]  # valore di default
            to_divide = min(candidates)

            for i, _ in enumerate(to_print):
                if i % (to_divide + 1) == 0:
                    to_print.insert(i, ''.center(50, '-'))

        s += '\n\n'.join(to_print)
        return indent(s, indent_amount)


class Unity(Base):
    def __init__(self, number, name, duration):
        self.name = name.upper().strip()
        self.number = number
        self.duration = duration
        self.modules = []

    def add_module(self, module):
        self.modules.append(module)

    def check(self):
        assert self.modules, 'No module found for UF {}'.format(self.name)

        for module in self.modules:
            module.check()

    def __str__(self):
        return self.str()

    def str(self, **kwargs):
        indent_amount = kwargs.get('indent', 0)
        assert indent_amount >= 0

        s = 'UNITà FUNZIONALE {}: {} - Durata {} Ore\n'.upper().format(self.number + 1, self.name, self.duration)
        s += 'MODULI (NUMERO): {}\n'.format(len(self.modules))
        s += '\n\n'.join([m.str(**kwargs) for m in self.modules])

        return indent(s, indent_amount)


class Document(Base):
    def __init__(self, name):
        self.name = name
        self.unities = []

    def add_unity(self, unity):
        self.unities.append(unity)

    def check(self):
        assert self.unities, 'No functional unity found for document {}'.format(self.name)

        for unity in self.unities:
            unity.check()

    def __str__(self):
        return self.str()

    def str(self, **kwargs):
        s = 'DOCUMENTO {}\n'.format(self.name)
        s += 'UNITà FUNZIONALI (NUMERO): {}\n'.upper().format(len(self.unities))
        s += '\n\n'.join([uf.str(**kwargs) for uf in self.unities])
        return s

    def print_questions(self, filepath=None, **kwargs):
        ordered = kwargs.get('ordered', True)
        separated = kwargs.get('separated', True)

        s = self.str(ordered=ordered, separated=separated)

        if not filepath:
            print(s)
        else:
            if isinstance(filepath, str) and not filepath.endswith('.txt'):
                filepath += '.txt'
                filepath = 'generated/' + filepath
            elif isinstance(filepath, pathlib.Path):
                filepath = filepath.with_suffix('.txt').name
                filepath = pathlib.Path('generated') / filepath

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(s)
            print('Questions written on', filepath)
        return s
