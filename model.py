import html


class Answer:
    def __init__(self, string):
        string = string.strip()
        self.text = '-'.join(string.split('-')[1:]).strip()
        self.is_correct = 'ok' in string.lower().split('-')[0]
        self.html = '<p>{}</p>'.format(html.escape(self.text, False))
        if self.is_correct:
            self.html = '<input type="hidden" id="Corretta">\n' + self.html


class Question:
    def __init__(self, name):
        self.name = name.strip()
        self.answers = []

    def set_answers(self, answers):
        self.answers = [a for a in answers]

    def add_answer(self, answer):
        self.answers.append(answer)

    def check(self, unity=None, module=None):
        where = ' question ' + self.name
        if module is not None:
            where = ' module ' + str(module + 1) + where
        if unity is not None:
            where = ' uf ' + str(unity + 1) + where

        where = where.strip()

        assert self.answers, 'No answer found. [{}]'.format(where)

        count_correct = sum(1 for ans in self.answers if ans.is_correct)
        assert count_correct > 0, 'No correct answer found. [{}]'.format(where)
        assert count_correct == 1, 'More than one correct answer found. [{}]'.format(where)


class Module:
    def __init__(self, name):
        name = ' '.join(name.split('(')[:-1]).strip()
        self.name = ' '.join([w.capitalize() for w in name.split()])
        self.questions = []

    def set_questions(self, questions):
        self.questions = [q for q in questions]

    def add_question(self, question):
        self.questions.append(question)

    def check(self):
        assert self.questions, 'No question found for module {}'.format(self.name)


class Unity:
    def __init__(self, name):
        self.name = name.upper().strip()
        self.modules = []

    def set_modules(self, modules):
        self.modules = [m for m in modules]

    def add_module(self, module):
        self.modules.append(module)

    def check(self, unity=None):
        assert self.modules, 'No module found for UF {}'.format(self.name)
        for i, module in enumerate(self.modules):
            module.check()
            for q in module.questions:
                q.check(unity=unity, module=i)
