from collections import defaultdict
import pathlib
import docx
import re

from xml_builder import generate_xmls_per_module
import model


def populate_document(doc_pathlib):
    counts = defaultdict(int)
    uf_before, module_before, question_before = [None] * 3
    model_doc = model.Document(doc_pathlib.stem)
    try:
        parsed_doc = docx.Document(str(doc_pathlib))
    except Exception as e:
        raise ValueError(str(e) + '. Documento Word non valido?')

    for paragraph in parsed_doc.paragraphs:
        text = paragraph.text
        # eliminiamo caratteri unicode che danno problemi
        text = text.replace('–', '-').replace('’', "'").replace('‘', "'")
        test = text.lower()

        if test.startswith('uf.'):
            name = ':'.join(text.split(':')[1:]).strip()
            uf = model.Unity(name, counts['uf'])
            model_doc.add_unity(uf)

            uf_before = uf
            module_before, question_before = [None] * 2

            counts['uf'] += 1
            for kw in ('module', 'question'):
                counts[kw] = 0

        elif test.startswith('modulo '):
            assert uf_before, 'Found module without unity!'

            name = text.split('-')[1].strip()
            module = model.Module(name, counts['module'], unity=uf_before)
            uf_before.add_module(module)

            module_before = module
            question_before = None

            counts['module'] += 1
            counts['question'] = 0

        elif test.startswith('domanda:'):
            assert module_before, 'Found question without module!'

            name = ':'.join(text.split(':')[1:])
            question = model.Question(name, counts['question'], module=module_before)
            module_before.add_question(question)

            question_before = question

            counts['question'] += 1

        elif test.startswith('risposta'):
            assert question_before, 'Found answer without question!'
            answer = model.Answer(text)
            question_before.add_answer(answer)

        elif test.replace('*', '').strip().startswith('slide'):
            assert question_before, 'Found jump to slide without question!'
            slides = set([int(el) for el in re.findall(r'(\d+)', test)])
            question_before.set_jump2slides(slides)

    return model_doc


# begin main
q_dir = pathlib.Path('questions_dir')
files = list(q_dir.rglob('*.docx')) + list(q_dir.rglob('*.doc'))

for file in files:
    print('start work on', file)
    doc = populate_document(file)
    doc.check()
    # print(doc)
    generate_xmls_per_module(doc)
