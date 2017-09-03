'''Fix error words extracted from highlights.

It seems that the combinations "fl" and "fi" mostly fail from text extraction by
pdfminer. E.g. 'first', 'flux', 'deficiency' will be u'\\ufb01rst', 
u'\\ufb02ux' and u'de\\ufb01ciency'.



# Copyright 2016 Guang-zhi XU
#
# This file is distributed under the terms of the
# GPLv3 licence. See the LICENSE file for details.
# You may use, distribute and modify this code under the
# terms of the GPLv3 license.

Update time: 2016-04-01 16:00:57.
'''


import re


_tilder_re=re.compile('\u02dc', re.UNICODE)
_fl_re=re.compile('\ufb02', re.UNICODE)
_fi_re=re.compile('\ufb01', re.UNICODE)
_ft_re=re.compile('\ufb05', re.UNICODE)
_single_quote1_re=re.compile('\u2018', re.UNICODE)
_single_quote2_re=re.compile('\u2019', re.UNICODE)
_double_quote1_re=re.compile('\u201c', re.UNICODE)
_double_quote2_re=re.compile('\u201d', re.UNICODE)
_single_dash_re=re.compile('\u2013', re.UNICODE)

KNOWN_LIST={\
        _tilder_re: '',\
        _fl_re: 'fl',\
        _fi_re: 'fi',\
        _ft_re: 'ft',\
        _single_quote1_re: "'",\
        _single_quote2_re: "'",\
        _double_quote1_re: '"',\
        _double_quote2_re: '"',\
        _single_dash_re: '--'\
        }


def fixWord(text):
    for reii,replaceii in list(KNOWN_LIST.items()):
        text=reii.sub(replaceii,text)

    return text







