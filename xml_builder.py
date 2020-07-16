from lxml.etree import Element, SubElement, tostring, parse, XMLSchema, CDATA
import os


def make_xml(module, fname=None):
    if fname is None:
        fname = module.name.lower().replace('/', '').replace(',', ' ').replace(':', ' ').replace('.', ' ')
        fname = '_'.join(fname.split())
        fname = 'domande_generate_{}'.format(fname)

    fname = fname.lower()
    if not fname.endswith('.xml'):
        fname += '.xml'

    schema_fname = os.path.join(os.getcwd(), 'schema.xsd')
    schema_doc = parse(schema_fname)
    schema = XMLSchema(schema_doc)

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
    schema.assertValid(root)

    # write to xml obj
    xml_obj = tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')

    # write to xml file
    generated_dir = os.path.join(os.getcwd(), 'generated')
    os.makedirs(generated_dir, exist_ok=True)
    with open(os.path.join(generated_dir, fname), 'wb') as f:
        f.write(xml_obj)

    print(fname, 'written into', generated_dir)
