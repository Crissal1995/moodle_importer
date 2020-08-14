import html
import textwrap
import sys


def indent(text, amount, ch=' '):
    return textwrap.indent(text, amount * ch)


class Answer:
    def __init__(self, name, is_correct):
        self.text = name.strip()
        self.is_correct = is_correct

        self.html_escaped = '<p>{}</p>'.format(html.escape(self.text, False))
        self.html = '<p>{}</p>'.format(self.text)

        if self.is_correct:
            to_add = '<input type="hidden" id="Corretta">\n'
            self.html_escaped = to_add + self.html_escaped
            self.html = to_add + self.html

    def __str__(self):
        return 'RISPOSTA{e}: {r}'.format(e=' ESATTA' if self.is_correct else '', r=self.text)


class Question:
    def __init__(self, name, number, module):
        self.name = name.strip()
        self.number = number
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
        where = 'uf: {u}, module: {m}, question: {q}'.format(
            u=self.module.unity.number + 1,
            m=self.module.number + 1,
            q=self.number + 1
        )
        assert self.answers, 'No answer found. [{}]'.format(where)

        count_correct = sum(1 for ans in self.answers if ans.is_correct)
        assert count_correct > 0, 'No correct answer found. [{}]'.format(where)
        assert count_correct == 1, 'More than one correct answer found. [{}]'.format(where)

        assert self.jump2slide, 'No slide to jump in case of error. [{}]'.format(where)

    def __str__(self):
        s = 'DOMANDA {n}: {text}\n'.format(n=self.number + 1, text=self.name)
        s += '\n'.join([str(ans) for ans in self.answers])
        s += '\nSE ERRORE, SALTA A {}'.format(self.jump2slide)
        # stampa tutte le slides a cui saltare, se sono più di una
        s += '{}'.format(' ' + str(self.jump2slides) if len(self.jump2slides) > 1 else '')
        return indent(s, 6)


class Module:
    def __init__(self, name, number, unity):
        name = ' '.join(name.split('(')[:-1]).strip()
        name = name.replace('/', ' e ')
        self.name = ' '.join([w.capitalize() for w in name.split()])
        self.number = number
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
        return self._str(False, False)

    def _str(self, *args, **kwargs):
        ordered = kwargs['ordered']
        separated = kwargs['separated']
        s = 'MODULO {n}: {t}\n'.format(n=self.number + 1, t=self.name)
        s += 'DOMANDE (NUMERO): {}\n'.format(len(self.questions))
        # cambiando l'array, cambia l'ordine della stampa delle domande
        qs = self.questions_sorted if ordered else self.questions
        to_print = [str(q) for q in qs]
        if separated:
            for i, _ in enumerate(to_print):
                if i == 0:
                    continue
                if i % 5 == 0:
                    to_print.insert(i, ''.center(50, '-'))
        s += '\n\n'.join(to_print)
        return indent(s, 3)


class Unity:
    def __init__(self, name, number):
        self.name = name.upper().strip()
        self.number = number
        self.modules = []

    def add_module(self, module):
        self.modules.append(module)

    def check(self):
        assert self.modules, 'No module found for UF {}'.format(self.name)

        for module in self.modules:
            module.check()

    def __str__(self):
        s = 'UNITà FUNZIONALE {}: {}\n'.upper().format(self.number + 1, self.name)
        s += 'MODULI (NUMERO): {}\n'.format(len(self.modules))
        s += '\n\n'.join([str(m) for m in self.modules])
        return s

    def _str(self, *args, **kwargs):
        s = 'UNITà FUNZIONALE {}: {}\n'.upper().format(self.number + 1, self.name)
        s += 'MODULI (NUMERO): {}\n'.format(len(self.modules))
        s += '\n\n'.join([m._str(*args, **kwargs) for m in self.modules])
        return s


class Document:
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
        s = 'DOCUMENTO {}\n'.format(self.name)
        s += 'UNITà FUNZIONALI (NUMERO): {}\n'.upper().format(len(self.unities))
        s += '\n\n'.join([str(uf) for uf in self.unities])
        return s

    def print_questions(self, ordered=False, separated=False):
        s = 'DOCUMENTO {}\n'.format(self.name)
        s += 'UNITà FUNZIONALI (NUMERO): {}\n'.upper().format(len(self.unities))
        s += '\n\n'.join([uf._str(ordered=ordered, separated=separated) for uf in self.unities])
        print(s)
        return s
