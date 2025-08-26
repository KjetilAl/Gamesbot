
import logging
import odf.namespaces
import odf.opendocument
import odf.table
import odf.text
import os
import os.path
import pprint
import subprocess
import unittest

import score_parser

logging.basicConfig(level=os.environ.get('LOG_LEVEL', logging.INFO))
log = logging.getLogger(__name__)

EXAMPLES_ODS    = "Minigame Scores Examples.ods"

def stat_or_none(filepath):
    """Like `os.stat`, but returns None if the file does not exist"""
    try:
        stat = os.stat(filepath)
        return stat
    except FileNotFoundError:
        return None

def soffice_convert(filepath, to_ext):
    """Asks soffice to convert one ODF file to another format"""
    dirname = os.path.dirname(filepath)
    basename = os.path.basename(filepath)
    return subprocess.run(['soffice', '--convert-to', to_ext, basename],
                cwd=dirname)

def soffice_refresh_fods(ods_path):
    """Refreshes a .ods/.fods pair from whichever is newer"""

    dirname = os.path.dirname(ods_path)
    root, ext = os.path.splitext(ods_path)
    fods_name = root + ".fods"

    opath = ods_path
    fpath = os.path.join(dirname, fods_name)

    ostat = stat_or_none(opath)
    fstat = stat_or_none(fpath)

    if not fstat and not ostat:
        raise Exception(f"file not found: {ods_path} or .fods")

    # Updated FODS: refresh the ODS
    if fstat and (not ostat or ostat.st_mtime_ns < fstat.st_mtime_ns):
        log.info(f"updating {opath}")
        soffice_convert(fpath, "ods")
        os.utime(opath, ns=(fstat.st_atime_ns, fstat.st_mtime_ns))

    # Updated ODS: refresh the FODS.
    elif ostat and (not fstat or fstat.st_mtime_ns < ostat.st_mtime_ns):
        log.info(f"updating {fpath}")
        soffice_convert(opath, "fods")
        os.utime(fpath, ns=(ostat.st_atime_ns, ostat.st_mtime_ns))

    elif ostat.st_mtime_ns == fstat.st_mtime_ns:
        log.info(f"times are synced for {root}.{{ods,fods}}")

    else:
        raise Exception(f"unreachable state comparing {opath}")

    return

def cell_node_string_content(cellElement):
    """Extracts a string value from a ODF table cell element

    In ODF XML, each table-cell has a child of type 'p' containing the actual
    text of the cell. Multi-line cells have multiple 'p' children, one for each
    line. This function extracts the text from the 'p' elements into a string
    value, preserving multi-line strings.
    """
    para_lines = []
    for p in cellElement.getElementsByType(odf.text.P):
        text = str(p)
        para_lines.append(text)
    return "\n".join(para_lines)

def cell_node_value(cellElement):
    """Extracts the value of an ODF table cell element """
    value_type = cellElement.getAttrNS(odf.namespaces.OFFICENS, "value-type")
    formula = cellElement.getAttrNS(odf.namespaces.TABLENS, 'formula')
    valattr = cellElement.getAttribute("value")
    celltext = cell_node_string_content(cellElement)

    if value_type is None:
        return None

    elif value_type == "string":
        value = cell_node_string_content(cellElement)

    elif value_type == 'float':

        if formula == 'of:=TRUE()':     value = True
        elif formula == 'of:=FALSE()':  value = False
        elif '.' not in valattr:        value = int(valattr)
        else:                           value = float(valattr)

    elif value_type == 'time':
        # TODO: Parse time text
        value = celltext

    else:
        value = celltext
        log.warn(f"Unparsed spreadsheet value type: {value_type!r}; text {value!r}")

    return value

def odf_expand_repeated(cellIterable):
    """Iteration helper: repeats cells with 'number-columns-repeated' attribute"""
    for cell in cellIterable:
        repeat_attr = cell.getAttrNS(odf.namespaces.TABLENS, 'number-columns-repeated')
        if repeat_attr is None:
            yield cell
        else:
            repeat = int(repeat_attr)
            while repeat:
                #log.debug(f"repeating cell countdown {repeat}")
                repeat -= 1
                yield cell

def spreadsheet_xml_to_dict(odf_doc):
    """Walks an ODF spreadsheet's XML and converts it to simple Python data"""
    sheets = {}
    for table in odf_doc.getElementsByType(odf.table.Table):
        name = table.getAttribute('name')
        records = []

        rows = table.getElementsByType(odf.table.TableRow).__iter__()

        # Parse the first row as a header
        hrow = rows.__next__()
        header = []
        for cell in hrow.getElementsByType(odf.table.TableCell):
            contents = cell_node_string_content(cell)
            header.append(contents)

        # For every row after the header:
        for row in rows:
            record = {}
            # For each cell in the row:
            for i, cell in enumerate(odf_expand_repeated(
                            row.getElementsByType(odf.table.TableCell))):

                # Ignore cells at end of row that have no matching header
                if len(header) <= i: break

                # Add cell contents to record
                key = header[i]
                value = cell_node_value(cell)
                if value is not None:
                    record[key] = value

            if record:
                log.debug(f"ODF row: {record!r}")
                records.append(record)

        sheets[name] = records

    return sheets

class TestExamplesSheet(unittest.TestCase):
    """Test cases against the ODF spreadsheet"""

    @classmethod
    def setUpClass(cls):
        script_dir = os.path.dirname(__file__)
        cls.fods_name = "Minigame Scores Examples.fods"
        cls.fods_path = os.path.join(script_dir, cls.fods_name)

        # soffice_refresh_fods(cls.ods_path)

        cls.doc = odf.opendocument.load(cls.fods_path)
        cls.sheets = spreadsheet_xml_to_dict(cls.doc)
        # log.debug(pprint.pformat(cls.sheets))

    @classmethod
    def findSheet(cls, sheet_name):
        for sheet in cls.sheets:
            if sheet.getAttribute("name") == sheet_name:
                return sheet
            else:
                raise Exception(f"{cls.ods_name!r} has no sheet named {sheet_name!r}")

    def do_parse_test(self, sheet, parsefn, matchfields):
        failed = []

        for example in sheet:
            parsed = parsefn(example['share_text'])
            if not parsed:
                raise Exception(f"{parsefn!r} returned {parsed!r} for example:\n{example['share_text']}")
            show_example = {}
            show_parsed = {}
            mismatched = []
            for field in matchfields:
                if field in parsed: show_parsed[field] = parsed[field]
                if field in example: show_example[field] = example[field]
                if field in example and (field not in parsed or example[field] != parsed[field]):
                    mismatched.append(field)

            if mismatched:
                raise AssertionError(f"""Parse mistmatch:

{example['share_text']}

Expected:   {show_example}
Got:        {show_parsed}
Mismatched fields:  {mismatched}
Full example object:
    {example}
Full parsed object:
    {parsed}
""")

    def test_parse_wordle_score(self):
        self.do_parse_test(
            sheet = self.sheets['Wordle'],
            parsefn = score_parser.parse_wordle_score,
            matchfields = ['game_number', 'attempts', 'solved', 'hard_mode', 'skill', 'luck'])

    def test_parse_connections_result(self):
        self.do_parse_test(
            sheet = self.sheets['Connections'],
            parsefn = score_parser.parse_connections_result,
            matchfields = ['game_number', 'num_guesses'])

    def test_parse_framed_score(self):
        self.do_parse_test(
            sheet = self.sheets['Framed'],
            parsefn = score_parser.parse_framed_score,
            matchfields = ['game_number', 'attempts', 'solved'])

    def test_parse_gisnep_score(self):
        self.do_parse_test(
            sheet = self.sheets['Gisnep'],
            parsefn = score_parser.parse_gisnep_score,
            matchfields = ['game_number', 'completion_time'])

    def test_parse_bandle_score(self):
        self.do_parse_test(
            sheet = self.sheets['Bandle'],
            parsefn = score_parser.parse_bandle_score,
            matchfields = ['game_number', 'attempts', 'solved', 'bonus_rounds_completed', 'bonus_rounds_total', 'bonus_emojis', 'current_streak', 'max_streak'])

class TestPipsParser(unittest.TestCase):
    def test_calculate_pips_score(self):
        # Test cases for easy difficulty
        self.assertEqual(score_parser.calculate_pips_score('easy', 10), 10)
        self.assertEqual(score_parser.calculate_pips_score('easy', 20), 10)
        self.assertEqual(score_parser.calculate_pips_score('easy', 21), 8)
        self.assertEqual(score_parser.calculate_pips_score('easy', 40), 8)
        self.assertEqual(score_parser.calculate_pips_score('easy', 60), 6)
        self.assertEqual(score_parser.calculate_pips_score('easy', 120), 4)
        self.assertEqual(score_parser.calculate_pips_score('easy', 180), 2)
        self.assertEqual(score_parser.calculate_pips_score('easy', 181), 1)

        # Test cases for medium difficulty
        self.assertEqual(score_parser.calculate_pips_score('medium', 40), 10)
        self.assertEqual(score_parser.calculate_pips_score('medium', 80), 8)
        self.assertEqual(score_parser.calculate_pips_score('medium', 120), 6)
        self.assertEqual(score_parser.calculate_pips_score('medium', 160), 4)
        self.assertEqual(score_parser.calculate_pips_score('medium', 200), 2)
        self.assertEqual(score_parser.calculate_pips_score('medium', 201), 1)

        # Test cases for hard difficulty
        self.assertEqual(score_parser.calculate_pips_score('hard', 60), 10)
        self.assertEqual(score_parser.calculate_pips_score('hard', 120), 8)
        self.assertEqual(score_parser.calculate_pips_score('hard', 180), 6)
        self.assertEqual(score_parser.calculate_pips_score('hard', 240), 4)
        self.assertEqual(score_parser.calculate_pips_score('hard', 300), 2)
        self.assertEqual(score_parser.calculate_pips_score('hard', 301), 1)

    def test_parse_pips_score(self):
        # Test case 1: Easy, no cookie
        message = "Pips #1 Easy 🟢\n0:36"
        expected = {
            "game_number": 1,
            "difficulty": "easy",
            "completion_time": 36,
            "score": 8,
            "cookie": False
        }
        self.assertEqual(score_parser.parse_pips_score(message), expected)

        # Test case 2: Medium, with cookie
        message = "Pips #1 Medium 🟡\n1:35 🍪"
        expected = {
            "game_number": 1,
            "difficulty": "medium",
            "completion_time": 95,
            "score": 6,
            "cookie": True
        }
        self.assertEqual(score_parser.parse_pips_score(message), expected)

        # Test case 3: Hard, no cookie
        message = "Pips #1 Hard 🔴\n3:37"
        expected = {
            "game_number": 1,
            "difficulty": "hard",
            "completion_time": 217,
            "score": 4,
            "cookie": False
        }
        self.assertEqual(score_parser.parse_pips_score(message), expected)

        # Test case 4: Invalid message
        message = "This is not a pips score"
        self.assertIsNone(score_parser.parse_pips_score(message))

    def test_is_pips_message(self):
        self.assertTrue(score_parser.is_pips_message("Pips #1 Easy 🟢\n0:36"))
        self.assertTrue(score_parser.is_pips_message("Pips #123 Hard 🔴\n10:00 🍪"))
        self.assertFalse(score_parser.is_pips_message("This is not a pips score"))
        self.assertFalse(score_parser.is_pips_message("Pips #1 Easy\n0:36")) # Missing emoji
