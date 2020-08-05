from collections import defaultdict
from xml_builder import make_xml
import docx
import re
from model import *

filepath = 'domande_old.docx'
doc = docx.Document(filepath)

unities = []
uf_before, module_before, question_before = None, None, None
counts = defaultdict(int)

for paragraph in doc.paragraphs:
    text = paragraph.text
    # eliminiamo caratteri unicode che danno problemi
    text = text.replace('–', '-').replace('’', "'").replace('‘', "'")
    test = text.lower()

    if test.startswith('uf.'):
        name = ':'.join(text.split(':')[1:]).strip()
        uf = Unity(name, counts['uf'])
        unities.append(uf)
        uf_before = uf
        counts['uf'] += 1
        for kw in ('module', 'question'):
            counts[kw] = 0

    elif test.startswith('modulo '):
        assert uf_before, 'Found module without unity!'
        name = text.split('-')[1].strip()
        module = Module(name, counts['module'], unity=uf_before)
        uf_before.add_module(module)
        module_before = module
        counts['module'] += 1
        counts['question'] = 0

    elif test.startswith('domanda:'):
        assert module_before, 'Found question without module!'
        name = ':'.join(text.split(':')[1:])
        question = Question(name, counts['question'], module=module_before)
        module_before.add_question(question)
        question_before = question
        counts['question'] += 1

    elif test.startswith('risposta'):
        assert question_before, 'Found answer without question!'
        answer = Answer(text)
        question_before.add_answer(answer)

    elif test.replace('*', '').strip().startswith('slide'):
        assert question_before, 'Found jump to slide without question!'
        slides = set([int(el) for el in re.findall(r'(\d*)', test) if el])
        question_before.set_jump2slides(slides)

# assert di correttezza del word parserizzato
for i, unity in enumerate(unities):
    unity.check()

# generazione di un xml per ogni modulo
for unity in unities:
    for module in unity.modules:
        i, j = unity.number, module.number
        name = 'uf_{}_module_{}'.format(i+1, j+1)
        make_xml(module, name)
