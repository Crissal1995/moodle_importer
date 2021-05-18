import html
import os
from typing import Union, Sequence
from collections import defaultdict
import textwrap
import pathlib
from abc import ABC
import re
from collections import Counter
from sklearn.cluster import AgglomerativeClustering as Clustering
import numpy as np
import json


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

    @property
    def htmlstr(self):
        return self.html

    def todict(self):
        return dict(
            is_correct=bool(self.is_correct),
            text=self.text,
            html=self.html,
        )


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

        self.answers.sort(key=lambda ans: not ans.is_correct)

    def check(self):
        where = 'uf: {u}, module: {m}, question: {q} / global question: {gq}'.format(
            u=self.module.unity.number + 1,
            m=self.module.number + 1,
            q=self.number + 1,
            gq=self.global_number + 1
        )
        assert self.answers, 'No answer found. [{}]'.format(where)
        assert len(self.answers) == 3, 'More than 3 answers found (maybe missing "DOMANDA:"?). [{}]'.format(where)

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

    def todict(self):
        return dict(
            name=self.name,
            number=self.number + 1,
            global_number=self.global_number + 1,
            jump2slide=self.jump2slide,
            answers=[answer.todict() for answer in self.answers]
        )


class QuestionCluster(Base):
    """Cluster of Questions"""

    questions = []
    min_jump2slide = None
    max_jump2slide = None

    def add_question(self, question: Question):
        """Add a question to the cluster"""
        self.questions.append(question)

        # set minimum j2s of cluster
        if not self.min_jump2slide:
            self.min_jump2slide = question.jump2slide
        else:
            self.min_jump2slide = min([question.jump2slide for question in self.questions])

        # set minimum j2s of cluster
        if not self.max_jump2slide:
            self.max_jump2slide = max(question.jump2slides)
        else:
            self.max_jump2slide = max([max(question.jump2slides) for question in self.questions])

    def set_questions(self, questions: Sequence[Question]):
        """Set a sequence of questions as Cluster questions"""
        self.questions = list(questions)

        self.min_jump2slide = min([question.jump2slide for question in self.questions])
        self.max_jump2slide = max([question.jump2slide for question in self.questions])

    def check(self):
        """Check sanity cluster"""
        for question in self.questions:
            question.check()

    def todict(self):
        return dict(
            min_slide_in_cluster=self.min_jump2slide,
            max_slide_in_cluster=self.max_jump2slide,
            count_questions=len(self.questions),
            questions=[question.todict() for question in self.questions]
        )

    def write_to_file(self, jsonpath: Union[str, os.PathLike]):
        jsonpath = pathlib.Path(jsonpath)

        with open(jsonpath.with_suffix(".json"), "w") as f:
            json.dump(self.todict(), f)


class Module(Base):
    def __init__(self, number, name, duration, unity):
        self.name = re.sub(r'\s+', ' ', name.replace('/', ' e ').strip())
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

    def create_clusters(self) -> Sequence[QuestionCluster]:
        # take sorted questions (doesn't change clustering)
        questions = self.questions_sorted

        # create ndarray
        X = np.array([q.jump2slide for q in questions]).reshape(-1, 1)

        # media di clusters di 5 o 6 elementi
        # max() per imporre minimo = 1
        n = max(len(questions) // 5, 1)

        # do agglomerative clustering
        linkage = "ward"
        labels = Clustering(n, linkage=linkage).fit_predict(X)
        treshold = 3
        while n and any(value < treshold for value in Counter(labels).values()):
            n -= 1
            labels = Clustering(n, linkage=linkage).fit_predict(X)

        if any(value < treshold for value in Counter(labels).values()):
            msg = f"Cannot find clustering with counts labels >= {treshold}"
            raise RuntimeError(msg)

        # create a list of questions for each label found by clustering
        questions_lists = defaultdict(list)

        for question, label in zip(questions, labels):
            questions_lists[label].append(question)

        clusters = []
        for label, questions_list in questions_lists.items():
            cluster = QuestionCluster()
            cluster.set_questions(questions_list)
            clusters.append(cluster)

        return clusters

    def write_cluster(self):
        clusters = self.create_clusters()

        thedict = dict(
            count_clusters=len(clusters),
            clusters=[cluster.todict() for cluster in clusters]
        )

        name = f"uf_{self.unity.number + 1}_m_{self.number + 1}.json"
        path = pathlib.Path("generated") / "cluster_json"

        # create path
        os.makedirs(path, exist_ok=True)

        # and set it to json file
        path /= name

        with open(path, "w", encoding="utf-8") as f:
            json.dump(thedict, f, indent=2, ensure_ascii=False)

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
            if Clustering:
                X = np.array([q.jump2slide for q in qs]).reshape(-1, 1)
                # media di clusters di 5 o 6 elementi
                n = len(qs) // 5
                if n < 1:
                    n = 1
                labels = Clustering(n, linkage='complete').fit_predict(X)
                old_label = None
                cnt = 0
                for i, label in enumerate(labels):
                    if old_label is None:
                        old_label = label
                        continue
                    elif label != old_label:
                        to_print.insert(i + cnt, ''.center(50, '-'))
                        cnt += 1
                    old_label = label
            else:
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
