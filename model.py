import html


class Answer:
    def __init__(self, string):
        string = string.strip()
        self.text = '-'.join(string.split('-')[1:]).strip()

        self.is_correct = 'ok' in string.lower().split('-')[0]

        self.html_escaped = '<p>{}</p>'.format(html.escape(self.text, False))
        self.html = '<p>{}</p>'.format(self.text)

        if self.is_correct:
            to_add = '<input type="hidden" id="Corretta">\n'
            self.html_escaped = to_add + self.html_escaped
            self.html = to_add + self.html


class Question:
    def __init__(self, name, number, module):
        self.name = name.strip()
        self.number = number
        self.answers = []
        self.module = module

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


class Module:
    def __init__(self, name, number, unity):
        name = ' '.join(name.split('(')[:-1]).strip()
        name = name.replace('/', ' e ')
        self.name = ' '.join([w.capitalize() for w in name.split()])
        self.number = number
        self.questions = []
        self.unity = unity

    def add_question(self, question):
        self.questions.append(question)

    def check(self):
        assert self.questions, 'No question found for module {}'.format(self.name)


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
            for q in module.questions:
                q.check()
