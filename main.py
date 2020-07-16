from model import *
from xml_builder import make_xml
import docx

filepath = 'domande.docx'
doc = docx.Document(filepath)

unities = []
uf_before, module_before, question_before = None, None, None

for paragraph in doc.paragraphs:
    t = paragraph.text

    if t.lower().startswith('uf.'):
        name = ':'.join(t.split(':')[1:]).strip()
        uf = Unity(name)
        unities.append(uf)
        uf_before = uf

    elif t.lower().startswith('modulo '):
        assert uf_before, 'Found module without unity!'
        name = t.split('-')[1].strip()
        module = Module(name)
        uf_before.add_module(module)
        module_before = module

    elif t.lower().startswith('domanda:'):
        assert module_before, 'Found question without module!'
        name = ':'.join(t.split(':')[1:])
        question = Question(name)
        module_before.add_question(question)
        question_before = question

    elif t.lower().startswith('risposta'):
        assert question_before, 'Found answer without question!'
        answer = Answer(t)
        question_before.add_answer(answer)

# assert di correttezza del word parserizzato
for i, unity in enumerate(unities):
    unity.check(unity=i)

for i, unity in enumerate(unities):
    for j, module in enumerate(unity.modules):
        name = 'uf_{}_module_{}'.format(i+1, j+1)
        make_xml(module, name)

