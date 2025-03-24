
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

def spreadsheet_xml_to_dict(odf_doc):
    """Walks an ODF spreadsheet's XML and converts it to simple Python data"""
    sheets = {}
    for table in odf_doc.getElementsByType(odf.table.Table):
        name = table.getAttribute('name')
        records = []

        rows = table.getElementsByType(odf.table.TableRow).__iter__()

        hrow = rows.__next__()
        header = []
        for cell in hrow.getElementsByType(odf.table.TableCell):
            contents = cell_node_string_content(cell)
            header.append(contents)

        for row in rows:
            record = {}
            for i, cell in enumerate(row.getElementsByType(odf.table.TableCell)):
                value = cell_node_value(cell)
                if value:
                    key = header[i]
                    record[key] = value

            if record:
                records.append(record)

        sheets[name] = records

    return sheets

class TestExamplesSheet(unittest.TestCase):
    """Test cases against the ODF spreadsheet"""

    @classmethod
    def setUpClass(cls):
        script_dir = os.path.dirname(__file__)
        cls.ods_name = EXAMPLES_ODS
        cls.ods_path = os.path.join(script_dir, cls.ods_name)

        soffice_refresh_fods(cls.ods_path)

        cls.doc = odf.opendocument.load(cls.ods_path)
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
            show_example = {}
            show_parsed = {}
            mismatched = []
            for field in matchfields:
                try:
                    show_parsed[field] = parsed[field]
                    show_example[field] = example[field]
                    if example[field] != parsed[field]:
                        mismatched.append(field)
                except KeyError:
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

    def test_connections_result(self):
        self.do_parse_test(
            sheet = self.sheets['Connections'],
            parsefn = score_parser.parse_connections_result,
            matchfields = ['puzzle_number', 'num_guesses'])
