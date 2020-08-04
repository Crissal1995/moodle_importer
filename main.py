from collections import defaultdict
from xml_builder import make_xml
import string
import docx
from model import *

filepath = 'domande_old.docx'
doc = docx.Document(filepath)

unities = []
uf_before, module_before, question_before = None, None, None
counts = defaultdict(int)

for paragraph in doc.paragraphs:
    t = paragraph.text
    # eliminiamo caratteri unicode che danno problemi
    t = t.replace('–', '-').replace('’', "'").replace('‘', "'")

    if t.lower().startswith('uf.'):
        name = ':'.join(t.split(':')[1:]).strip()
        uf = Unity(name, counts['uf'])
        unities.append(uf)
        uf_before = uf
        counts['uf'] += 1
        for kw in ('module', 'question'):
            counts[kw] = 0

    elif t.lower().startswith('modulo '):
        assert uf_before, 'Found module without unity!'
        name = t.split('-')[1].strip()
        module = Module(name, counts['module'], unity=uf_before)
        uf_before.add_module(module)
        module_before = module
        counts['module'] += 1
        counts['question'] = 0

    elif t.lower().startswith('domanda:'):
        assert module_before, 'Found question without module!'
        name = ':'.join(t.split(':')[1:])
        question = Question(name, counts['question'], module=module_before)
        module_before.add_question(question)
        question_before = question
        counts['question'] += 1

    elif t.lower().startswith('risposta'):
        assert question_before, 'Found answer without question!'
        answer = Answer(t)
        question_before.add_answer(answer)

    elif t.lower().replace('*', '').strip().startswith('slide'):
        assert question_before, 'Found jump to slide without question!'
        slide_pages = [el.replace('.', '').strip() for el in t.lower().split('n')[1:]]
        slide_pages = ' '.join(slide_pages).split('-')
        slide_pages = set([el.strip() for el in slide_pages for char in el if char in string.digits])
        question_before.set_jump2slides(slide_pages)
        print(question_before)
        print()

# assert di correttezza del word parserizzato
for i, unity in enumerate(unities):
    unity.check()

# generazione di un xml per ogni modulo
for unity in unities:
    for module in unity.modules:
        i, j = unity.number, module.number
        name = 'uf_{}_module_{}'.format(i+1, j+1)
        make_xml(module, name)
