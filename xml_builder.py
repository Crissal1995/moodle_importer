import os

from lxml.etree import Element, SubElement, tostring, parse, XMLSchema, CDATA
import pathlib
import warnings


def generate_xmls_per_module(doc, print_=True):
    for unity in doc.unities:
        for module in unity.modules:
            i, j = unity.number, module.number
            name = 'uf_{}_module_{}'.format(i+1, j+1)
            make_xml(module, name, doc.name, print_)


def make_xml(module, fname, docname, print_):
    fname = fname.lower()
    if not fname.endswith('.xml'):
        fname += '.xml'

    # root of the xml file
    root = Element('quiz')

    # category informations
    question = SubElement(root, 'question', {'type': 'category'})

    category = SubElement(question, 'category')
    text_category = SubElement(category, 'text')
    text_category.text = '$course$/top/{}'.format(module.name)

    info = SubElement(question, 'info', {'format': 'html'})
    text_info = SubElement(info, 'text')
    text_info.text = CDATA('<p>Domande per il modulo <span>{}</span></p>'.format(module.name))

    _ = SubElement(question, 'idnumber')

    # repeat for each question
    for i, q in enumerate(module.questions):
        question = SubElement(root, 'question', {'type': 'multichoice'})

        name = SubElement(question, 'name')
        text = SubElement(name, 'text')
        text.text = 'Domanda {}'.format(i+1)

        questiontext = SubElement(question, 'questiontext', {'format': 'html'})
        text = SubElement(questiontext, 'text')
        text.text = CDATA('<p>{}</p>'.format(q.name))

        generalfeedback = SubElement(question, 'generalfeedback', {'format': 'html'})
        _ = SubElement(generalfeedback, 'text')

        defaultgrade = SubElement(question, 'defaultgrade')
        defaultgrade.text = str(float(1))

        penalty = SubElement(question, 'penalty')
        penalty.text = str(float(1/3))

        hidden = SubElement(question, 'hidden')
        hidden.text = str(0)

        _ = SubElement(question, 'idnumber')

        single = SubElement(question, 'single')
        single.text = 'true'

        shuffleanswers = SubElement(question, 'shuffleanswers')
        shuffleanswers.text = 'true'

        answernumbering = SubElement(question, 'answernumbering')
        answernumbering.text = 'abc'

        correctfeedback = SubElement(question, 'correctfeedback', {'format': 'html'})
        text = SubElement(correctfeedback, 'text')
        text.text = 'Risposta corretta.'

        partiallycorrectfeedback = SubElement(question, 'partiallycorrectfeedback')
        text = SubElement(partiallycorrectfeedback, 'text')
        text.text = 'Risposta parzialmente corretta.'

        incorrectfeedback = SubElement(question, 'incorrectfeedback')
        text = SubElement(incorrectfeedback, 'text')
        text.text = 'Risposta errata.'

        _ = SubElement(question, 'shownumcorrect')

        for ans in q.answers:
            fraction = '100' if ans.is_correct else '0'

            answer = SubElement(question, 'answer', {'format': 'html', 'fraction': fraction})

            text = SubElement(answer, 'text')
            text.text = CDATA(ans.html)

            feedback = SubElement(answer, 'feedback', {'format': 'html'})
            text = SubElement(feedback, 'text')
            text.text = CDATA('<p>Risposta Esatta</p>' if ans.is_correct else '<p>Risposta Errata</p>')

    # assert xml generated is valid
    schema_path = pathlib.Path() / 'schema.xsd'
    if schema_path.exists():
        schema_tree = parse(str(schema_path))
        schema = XMLSchema(schema_tree)
        schema.assertValid(root)
    else:
        schema_warn = 'Cannot find schema.xsd in current directory, so validation cannot be made'
        warnings.warn(schema_warn, ResourceWarning)

    # write to xml obj
    xml_obj = tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')

    # write to xml file
    generated_dir = pathlib.Path() / 'generated' / docname / "questions_xml"
    os.makedirs(generated_dir, exist_ok=True)
    with open(generated_dir / fname, 'wb') as f:
        f.write(xml_obj)

    if print_:
        print(fname, 'written into', generated_dir)
