# Patches
# Maybe I'll need this, we'll see
# import py2neo
from py2neo.packages.httpstream.jsonstream \
    import (AwaitingData, UnexpectedCharacter, Tokeniser, EndOfStream)
# _Entity = py2neo.neo4j._Entity
# entity_patch_ftype = type(_Entity.get_properties)

def _read_digit(self):
    pos = self.data.tell()
    try:
        digit = self._read()
        if digit not in "0123456789eE-":
            self.data.seek(pos)
            raise UnexpectedCharacter(digit)
    except AwaitingData:
        self.data.seek(pos)
        raise AwaitingData()
    return digit

def _read_number(self):
    pos = self.data.tell()
    src = []
    has_fractional_part = False
    try:
        # check for sign
        ch = self._peek()
        if ch == '-':
            src.append(self._read())
        # read integer part
        ch = self._read_digit()
        src.append(ch)
        if ch != '0':
            while True:
                try:
                    src.append(self._read_digit())
                except (UnexpectedCharacter, EndOfStream):
                    break
        try:
            ch = self._peek()
        except EndOfStream:
            pass
        # read fractional part
        if ch == '.':
            has_fractional_part = True
            src.append(self._read())
            while True:
                try:
                    src.append(self._read_digit())
                except (UnexpectedCharacter, EndOfStream):
                    break
    except AwaitingData:
        # number potentially incomplete: need to wait for
        # further data or end of stream
        self.data.seek(pos)
        raise AwaitingData()
    src = "".join(src)
    if has_fractional_part:
        return src, float(src)
    else:
        return src, int(src)

# def entity_get_properties(self):
#     if not self.is_abstract:
#         size = 1024
#         response = self._properties_resource._get()._response
#         body = []
#         while True:
#             chunk = response.read(size)
#             if chunk:
#                 body.append(chunk)
#             else:
#                 break
            
#         logging.info('resources: %s' % body)
#         self._properties = json.loads(''.join(body))
#     return self._properties

# _Entity.get_properties = entity_get_properties
def patch():
    Tokeniser._read_digit = _read_digit
    Tokeniser._read_number = _read_number
