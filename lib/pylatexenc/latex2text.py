#
# The MIT License (MIT)
# 
# Copyright (c) 2015 Philippe Faist
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


import os
import re
import unicodedata
from . import latexwalker
import logging


logger = logging.getLogger(__name__);



class EnvDef:
    def __init__(self, envname, simplify_repl=None, discard=False):
        self.envname = envname
        self.simplify_repl = simplify_repl
        self.discard = discard

class MacroDef:
    def __init__(self, macname, simplify_repl=None, discard=None):
        """
        Arguments:
            - `macname`: the name of the macro (no backslash)
            - `simplify_repl`: either a string or a callable. The string
              may contain '%s' replacements, in which the macro arguments
              will be substituted. The callable should accept the
              :py:class:`~latexwalker.LatexMacroNode` as an argument.
        """
        if (isinstance(macname, MacroDef)):
            o = macname
            self.macname = o.macname
            self.discard = o.discard
            self.simplify_repl = o.simplify_repl
        elif (isinstance(macname, tuple)):
            (self.macname, self.simplify_repl) = macname
            self.discard = True if (discard is None) else discard ;
            if (simplify_repl is not None or discard is not None):
                raise ValueError("macname=%r is tuple but other parameters specified" %(macname,))
        else:
            self.macname = macname
            self.discard = True if (discard is None) else discard ;
            self.simplify_repl = simplify_repl


_default_env_list = [
    EnvDef('', discard=False), # default for unknown environments

    EnvDef('equation', discard=False),
    EnvDef('eqnarray', discard=False),
    EnvDef('align', discard=False),
    EnvDef('multline', discard=False),

    # spaces added so that database indexing doesn't index the word "array" or "pmatrix"
    EnvDef('array', simplify_repl='< a r r a y >'),
    EnvDef('pmatrix', simplify_repl='< p m a t r i x >'),
    EnvDef('bmatrix', simplify_repl='< b m a t r i x >'),
    EnvDef('smallmatrix', simplify_repl='< s m a l l m a t r i x >'),

    EnvDef('center', simplify_repl='\n%s\n'),
    EnvDef('flushleft', simplify_repl='\n%s\n'),
    EnvDef('flushright', simplify_repl='\n%s\n'),
    
    EnvDef('exenumerate', discard=False),
    EnvDef('enumerate', discard=False),
    EnvDef('list', discard=False),
    EnvDef('itemize', discard=False),
    EnvDef('subequations', discard=False),
    EnvDef('figure', discard=False),
    EnvDef('table', discard=False),
    ];


# NOTE: macro will only be assigned arguments if they are explicitely defined as accepting arguments
#       in latexwalker.py.

_default_macro_list = [
    MacroDef('', discard=True), # default for unknown macros

    MacroDef('textbf', discard=False),
    MacroDef('textit', discard=False),
    MacroDef('textsl', discard=False),
    MacroDef('textsc', discard=False),
    MacroDef('text', discard=False),
    MacroDef('mathrm', discard=False),

    # spaces added so that database indexing doesn't index the word "graphics"
    ('includegraphics', '< g r a p h i c s >'),

    ('ref', '<ref>'),
    ('eqref', '(<ref>)'),
    ('url', '<%s>'),
    ('item', lambda r: '\n  '+(latexnodes2text([r.nodeoptarg]) if r.nodeoptarg else '*')),
    ('footnote', '[%s]'),

    ('texorpdfstring', lambda node: latexnodes2text(node.nodeargs[1:2])), # use second argument

    ('oe', '\u0153'),
    ('OE', '\u0152'),
    ('ae', '\u00e6'),
    ('AE', '\u00c6'),
    ('aa', '\u00e5'), # a norvegien/nordique
    ('AA', '\u00c5'), # A norvegien/nordique
    ('o', '\u00f8'), # o norvegien/nordique
    ('O', '\u00d8'), # O norvegien/nordique
    ('ss', '\u00df'), # s-z allemand
    ('L', "\N{LATIN CAPITAL LETTER L WITH STROKE}"),
    ('l', "\N{LATIN SMALL LETTER L WITH STROKE}"),
    ('i', "\N{LATIN SMALL LETTER DOTLESS I}"),
    ('j', "\N{LATIN SMALL LETTER DOTLESS J}"),

    ("~", "~" ),
    ("&", "\\&" ), # HACK, see below for text replacement of '&'
    ("$", "$" ),
    ("{", "{" ),
    ("}", "}" ),
    ("%", lambda arg: "%" ), # careful: % is formatting substituion symbol...
    ("#", "#" ),
    ("_", "_" ),

    ("\\", '\n'),

    ("textquoteleft", "`"),
    ("textquoteright", "'"),
    ("textquotedblright", "\N{RIGHT DOUBLE QUOTATION MARK}"),
    ("textquotedblleft", "\N{LEFT DOUBLE QUOTATION MARK}"),
    ("textendash", "\N{EN DASH}"),
    ("textemdash", "\N{EM DASH}"),

    ('textpm', "\N{PLUS-MINUS SIGN}"),
    ('textmp', "\N{MINUS-OR-PLUS SIGN}"),

    ("texteuro", "\N{EURO SIGN}"),

    # math stuff

    ("hbar", "\N{LATIN SMALL LETTER H WITH STROKE}"),
    ("ell", "\N{SCRIPT SMALL L}"),

    ('forall', "\N{FOR ALL}"),
    ('complement', "\N{COMPLEMENT}"),
    ('partial', "\N{PARTIAL DIFFERENTIAL}"),
    ('exists', "\N{THERE EXISTS}"),
    ('nexists', "\N{THERE DOES NOT EXIST}"),
    ('varnothing', "\N{EMPTY SET}"),
    ('emptyset', "\N{EMPTY SET}"),
    # increment?
    ('nabla', "\N{NABLA}"),
    #
    ('in', "\N{ELEMENT OF}"),
    ('notin', "\N{NOT AN ELEMENT OF}"),
    ('ni', "\N{CONTAINS AS MEMBER}"),
    ('prod', '\N{N-ARY PRODUCT}'),
    ('coprod', '\N{N-ARY COPRODUCT}'),
    ('sum', '\N{N-ARY SUMMATION}'),
    ('setminus', '\N{SET MINUS}'),
    ('smallsetminus', '\N{SET MINUS}'),
    ('ast', '\N{ASTERISK OPERATOR}'),
    ('circ', '\N{RING OPERATOR}'),
    ('bullet', '\N{BULLET OPERATOR}'),
    ('sqrt', '\N{SQUARE ROOT}(%s)'),
    ('propto', '\N{PROPORTIONAL TO}'),
    ('infty', '\N{INFINITY}'),
    ('parallel', '\N{PARALLEL TO}'),
    ('nparallel', '\N{NOT PARALLEL TO}'),
    ('wedge', "\N{LOGICAL AND}"),
    ('vee', "\N{LOGICAL OR}"),
    ('cap', '\N{INTERSECTION}'),
    ('cup', '\N{UNION}'),
    ('int', '\N{INTEGRAL}'),
    ('iint', '\N{DOUBLE INTEGRAL}'),
    ('iiint', '\N{TRIPLE INTEGRAL}'),
    ('oint', '\N{CONTOUR INTEGRAL}'),

    ('sim', '\N{TILDE OPERATOR}'),
    ('backsim', '\N{REVERSED TILDE}'),
    ('simeq', '\N{ASYMPTOTICALLY EQUAL TO}'),
    ('approx', '\N{ALMOST EQUAL TO}'),
    ('neq', '\N{NOT EQUAL TO}'),
    ('equiv', '\N{IDENTICAL TO}'),
    ('ge', '>'),#
    ('le', '<'),#
    ('leq', '\N{LESS-THAN OR EQUAL TO}'),
    ('geq', '\N{GREATER-THAN OR EQUAL TO}'),
    ('leqslant', '\N{LESS-THAN OR EQUAL TO}'),
    ('geqslant', '\N{GREATER-THAN OR EQUAL TO}'),
    ('leqq', '\N{LESS-THAN OVER EQUAL TO}'),
    ('geqq', '\N{GREATER-THAN OVER EQUAL TO}'),
    ('lneqq', '\N{LESS-THAN BUT NOT EQUAL TO}'),
    ('gneqq', '\N{GREATER-THAN BUT NOT EQUAL TO}'),
    ('ll', '\N{MUCH LESS-THAN}'),
    ('gg', '\N{MUCH GREATER-THAN}'),
    ('nless', '\N{NOT LESS-THAN}'),
    ('ngtr', '\N{NOT GREATER-THAN}'),
    ('nleq', '\N{NEITHER LESS-THAN NOR EQUAL TO}'),
    ('ngeq', '\N{NEITHER GREATER-THAN NOR EQUAL TO}'),
    ('lesssim', '\N{LESS-THAN OR EQUIVALENT TO}'),
    ('gtrsim', '\N{GREATER-THAN OR EQUIVALENT TO}'),
    ('lessgtr', '\N{LESS-THAN OR GREATER-THAN}'),
    ('gtrless', '\N{GREATER-THAN OR LESS-THAN}'),
    ('prec', '\N{PRECEDES}'),
    ('succ', '\N{SUCCEEDS}'),
    ('preceq', '\N{PRECEDES OR EQUAL TO}'),
    ('succeq', '\N{SUCCEEDS OR EQUAL TO}'),
    ('precsim', '\N{PRECEDES OR EQUIVALENT TO}'),
    ('succsim', '\N{SUCCEEDS OR EQUIVALENT TO}'),
    ('nprec', '\N{DOES NOT PRECEDE}'),
    ('nsucc', '\N{DOES NOT SUCCEED}'),
    ('subset', '\N{SUBSET OF}'),
    ('supset', '\N{SUPERSET OF}'),
    ('subseteq', '\N{SUBSET OF OR EQUAL TO}'),
    ('supseteq', '\N{SUPERSET OF OR EQUAL TO}'),
    ('nsubseteq', '\N{NEITHER A SUBSET OF NOR EQUAL TO}'),
    ('nsupseteq', '\N{NEITHER A SUPERSET OF NOR EQUAL TO}'),
    ('subsetneq', '\N{SUBSET OF WITH NOT EQUAL TO}'),
    ('supsetneq', '\N{SUPERSET OF WITH NOT EQUAL TO}'),


    ('cdot', '\N{MIDDLE DOT}'),
    ('times', '\N{MULTIPLICATION SIGN}'),
    ('otimes', '\N{CIRCLED TIMES}'),
    ('oplus', '\N{CIRCLED PLUS}'),
    ('bigotimes', '\N{CIRCLED TIMES}'),
    ('bigoplus', '\N{CIRCLED PLUS}'),

    ('frac', '%s/%s'),
    ('nicefrac', '%s/%s'),

    ('cos', 'cos'),
    ('sin', 'sin'),
    ('tan', 'tan'),
    ('arccos', 'arccos'),
    ('arcsin', 'arcsin'),
    ('arctan', 'arctan'),

    ('prime', "'"),
    ('dag', "\N{DAGGER}"),
    ('dagger', "\N{DAGGER}"),
    ('pm', "\N{PLUS-MINUS SIGN}"),
    ('mp', "\N{MINUS-OR-PLUS SIGN}"),

    (',', " "),
    (';', " "),
    (':', " "),
    (' ', " "),
    ('!', ""), # sorry, no negative space in ascii
    ('quad', "  "),
    ('qquad', "    "),

    ('ldots', "..."),
    ('cdots', "..."),
    ('ddots', "..."),
    ('dots', "..."),
    
    ('langle', '\N{LEFT ANGLE BRACKET}'),
    ('rangle', '\N{RIGHT ANGLE BRACKET}'),
    ('mid', '|'),
    ('nmid', '\N{DOES NOT DIVIDE}'),
    
    ('ket', '|%s\N{RIGHT ANGLE BRACKET}'),
    ('bra', '\N{LEFT ANGLE BRACKET}%s|'),
    ('braket', '\N{LEFT ANGLE BRACKET}%s|%s\N{RIGHT ANGLE BRACKET}'),
    ('ketbra', '|%s\N{RIGHT ANGLE BRACKET}\N{LEFT ANGLE BRACKET}%s|'),
    ('uparrow', '\N{UPWARDS ARROW}'),
    ('downarrow', '\N{DOWNWARDS ARROW}'),
    ('rightarrow', '\N{RIGHTWARDS ARROW}'),
    ('to', '\N{RIGHTWARDS ARROW}'),
    ('leftarrow', '\N{LEFTWARDS ARROW}'),
    ('longrightarrow', '\N{LONG RIGHTWARDS ARROW}'),
    ('longleftarrow', '\N{LONG LEFTWARDS ARROW}'),

    # we use these conventions as Identity operator (\mathbbm{1})
    ('id', '\N{MATHEMATICAL DOUBLE-STRUCK CAPITAL I}'),
    ('Ident', '\N{MATHEMATICAL DOUBLE-STRUCK CAPITAL I}'),
    ];



def _format_uebung(n):
    s = '\n%s\n' %(latexnodes2text([n.nodeargs[0]]));
    optarg = n.nodeargs[1];
    if (optarg is not None):
        s += '[%s]\n' %(latexnodes2text([optarg]));
    return s


_default_macro_list += [
    # some ethuebung.sty macros
    ('exercise', _format_uebung),
    ('uebung', _format_uebung),
    ('hint', 'Hint: %s'),
    ('hints', 'Hints: %s'),
    ('hinweis', 'Hinweis: %s'),
    ('hinweise', 'Hinweise: %s'),
    ];





def _greekletters(letterlist):
    for l in letterlist:
        ucharname = l.upper()
        if (ucharname == 'LAMBDA'):
            ucharname = 'LAMDA'
        smallname = "GREEK SMALL LETTER "+ucharname;
        if (ucharname == 'EPSILON'):
            smallname = "GREEK LUNATE EPSILON SYMBOL"
        if (ucharname == 'PHI'):
            smallname = "GREEK PHI SYMBOL"
        _default_macro_list.append(
            (l, unicodedata.lookup(smallname))
            );
        _default_macro_list.append(
            (l[0].upper()+l[1:], unicodedata.lookup("GREEK CAPITAL LETTER "+ucharname))
            );
_greekletters( ('alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa',
                'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi',
                'chi', 'psi', 'omega') )
_default_macro_list += [
    ('varepsilon', '\N{GREEK SMALL LETTER EPSILON}'),
    ('vartheta', '\N{GREEK THETA SYMBOL}'),
    ('varpi', '\N{GREEK PI SYMBOL}'),
    ('varrho', '\N{GREEK RHO SYMBOL}'),
    ('varsigma', '\N{GREEK SMALL LETTER FINAL SIGMA}'),
    ('varphi', '\N{GREEK SMALL LETTER PHI}'),
    ]

unicode_accents_list = (
    # see http://en.wikibooks.org/wiki/LaTeX/Special_Characters for a list
    ("'", "\N{COMBINING ACUTE ACCENT}"),
    ("`", "\N{COMBINING GRAVE ACCENT}"),
    ('"', "\N{COMBINING DIAERESIS}"),
    ("c", "\N{COMBINING CEDILLA}"),
    ("^", "\N{COMBINING CIRCUMFLEX ACCENT}"),
    ("~", "\N{COMBINING TILDE}"),
    ("H", "\N{COMBINING DOUBLE ACUTE ACCENT}"),
    ("k", "\N{COMBINING OGONEK}"),
    ("=", "\N{COMBINING MACRON}"),
    ("b", "\N{COMBINING MACRON BELOW}"),
    (".", "\N{COMBINING DOT ABOVE}"),
    ("d", "\N{COMBINING DOT BELOW}"),
    ("r", "\N{COMBINING RING ABOVE}"),
    ("u", "\N{COMBINING BREVE}"),
    ("v", "\N{COMBINING CARON}"),

    ("vec", "\N{COMBINING RIGHT ARROW ABOVE}"),
    ("dot", "\N{COMBINING DOT ABOVE}"),
    ("hat", "\N{COMBINING CIRCUMFLEX ACCENT}"),
    ("check", "\N{COMBINING CARON}"),
    ("breve", "\N{COMBINING BREVE}"),
    ("acute", "\N{COMBINING ACUTE ACCENT}"),
    ("grave", "\N{COMBINING GRAVE ACCENT}"),
    ("tilde", "\N{COMBINING TILDE}"),
    ("bar", "\N{COMBINING OVERLINE}"),
    ("ddot", "\N{COMBINING DIAERESIS}"),

    ("not", "\N{COMBINING LONG SOLIDUS OVERLAY}"),

    );

def make_accented_char(node, combining):
    nodearg = node.nodeargs[0] if len(node.nodeargs) else latexwalker.LatexCharsNode(chars=' ')

    c = latexnodes2text([nodearg]).strip();

    def getaccented(ch, combining):
        ch = str(ch)
        combining = str(combining)
        if (ch == "\N{LATIN SMALL LETTER DOTLESS I}"):
            ch = "i"
        if (ch == "\N{LATIN SMALL LETTER DOTLESS J}"):
            ch = "j"
        #print u"Accenting %s with %s"%(ch, combining) # this causes UnicdeDecodeError!!!
        return unicodedata.normalize('NFC', str(ch)+combining)

    return "".join([getaccented(ch, combining) for ch in c]);


for u in unicode_accents_list:
    (mname, mcombining) = u;
    _default_macro_list.append(
        (mname, lambda x, c=mcombining: make_accented_char(x, c))
        );



default_env_dict = dict([(e.envname, e) for e in _default_env_list])
default_macro_dict = dict([(m.macname, m) for m in (MacroDef(m) for m in _default_macro_list)])

default_text_replacements = (
    # remove indentation provided by LaTeX
    #(re.compile(r'\n[ \t]*'), '\n'),
    
    ("~", " "),
    ("``", '"'),
    ("''", '"'),

    (r'(?<!\\)&', '   '), # ignore tabular alignments, just add a little space
    ('\\&', '&'), # but preserve the \& escapes, that we before *hackingly* kept as '\&' for this purpose ...

    )




# ------------------------------------------------------------------------------

class LatexNodes2Text(object):
    def __init__(self, env_dict=None, macro_dict=None, text_replacements=None, **flags):
        super(LatexNodes2Text, self).__init__()

        if env_dict is None:  env_dict = default_env_dict
        if macro_dict is None:  macro_dict = default_macro_dict
        if text_replacements is None: text_replacements = default_text_replacements

        self.env_dict = dict(env_dict)
        self.macro_dict = dict(macro_dict)
        self.text_replacements = text_replacements

        self.tex_input_directory = None
        self.strict_input = True

        self.keep_inline_math = flags.pop('keep_inline_math', False)
        self.keep_comments = flags.pop('keep_comments', False)
        if flags:
            # any flags left which we haven't recognized
            logger.warning("LatexNodes2Text(): Unknown flag(s) encountered: %r", list(flags.keys()))
        

    def set_tex_input_directory(self, tex_input_directory, latex_walker_init_args=None, strict_input=True):

        self.tex_input_directory = tex_input_directory
        self.latex_walker_init_args = latex_walker_init_args if latex_walker_init_args else {}
        self.strict_input = strict_input
        
        if tex_input_directory:
            self.macro_dict['input'] = MacroDef('input', lambda n: self._callback_input(n))
            self.macro_dict['include'] = MacroDef('include', lambda n: self._callback_input(n))
        else:
            self.macro_dict['input'] = MacroDef('input', discard=True)
            self.macro_dict['include'] = MacroDef('include', discard=True)


    def read_input_file(self, fn):
        fnfull = os.path.realpath(os.path.join(self.tex_input_directory, fn))
        if self.strict_input:
            # make sure that the input file is strictly within dirfull, and didn't escape with
            # '../..' tricks or via symlinks.
            dirfull = os.path.realpath(self.tex_input_directory)
            if not fnfull.startswith(dirfull):
                logger.warning("Can't access path '%s' leading outside of mandated directory [strict input mode]",
                               fn)
                return ''

        if not os.path.exists(fnfull) and os.path.exists(fnfull + '.tex'):
            fnfull = fnfull + '.tex'
        if not os.path.exists(fnfull) and os.path.exists(fnfull + '.latex'):
            fnfull = fnfull + '.latex'
        if not os.path.isfile(fnfull):
            logger.warning("Error, file doesn't exist: '%s'", fn)
            return ''
        
        try:
            with open(fnfull) as f:
                return f.read()
        except IOError as e:
            logger.warning("Error, can't access '%s': %s", fn, e)
            return ''


    def _callback_input(self, n):
        #
        # recurse into files upon '\input{}'
        #
        
        if (len(n.nodeargs) != 1):
            logger.warning(r"Expected exactly one argument for '\input' ! Got = %r", n.nodeargs)

        inputtex = self.read_input_file(self.nodelist_to_text([n.nodeargs[0]]).strip())

        return self.nodelist_to_text(latexwalker.LatexWalker(inputtex,
                                                             **self.latex_walker_init_args).get_latex_nodes()[0])


    def latex_to_text(self, latex, **parse_flags):
        """
        Parses the `latex` LaTeX code heuristically, and returns a text approximation of it.
        Suitable, e.g. for indexing in a database.

        The `parse_flags` are the flags to give on to the
        py:class:`~pylatexenc.latexwalker.LatexWalker` constructor.
        """
        return self.nodelist_to_text(latexwalker.LatexWalker(latex, **parse_flags).get_latex_nodes()[0])


    def nodelist_to_text(self, nodelist):
        """
        Extracts text from a node list. `nodelist` is a list of nodes as returned by
        `latexwalker.get_latex_nodes()`.
        """
    
        s = "".join( ( self.node_to_text(n) for n in nodelist ) )

        # now, perform suitable replacements
        for pattern, replacement in self.text_replacements:
            if (hasattr(pattern, 'sub')):
                s = pattern.sub(replacement, s)
            else:
                s = s.replace(pattern, replacement)

        #  ###TODO: more clever handling of math modes??

        if (not self.keep_inline_math):
            s = s.replace('$', ''); # removing math mode inline signs, just keep their Unicode counterparts..

        return s

    
    def node_to_text(self, node):
        if (node is None):
            return ""
        
        if (node.isNodeType(latexwalker.LatexCharsNode)):
            return node.chars
        
        if (node.isNodeType(latexwalker.LatexCommentNode)):
            if (self.keep_comments):
                return '%'+node.comment+'\n'
            return ""
        
        if (node.isNodeType(latexwalker.LatexGroupNode)):
            return "".join([self.node_to_text(n) for n in node.nodelist])
        
        if (node.isNodeType(latexwalker.LatexMacroNode)):
            # get macro behavior definition.
            macroname = node.macroname.rstrip('*');
            if (macroname in self.macro_dict):
                mac = self.macro_dict[macroname]
            else:
                # no predefined behavior, use default:
                mac = self.macro_dict['']
            if mac.simplify_repl:
                if (callable(mac.simplify_repl)):
                    return mac.simplify_repl(node)
                if ('%' in mac.simplify_repl):
                    try:
                        return mac.simplify_repl % tuple([self.node_to_text(nn) for nn in node.nodeargs])
                    except (TypeError, ValueError):
                        logger.warning("WARNING: Error in configuration: macro '%s' failed its substitution!",
                                       macroname);
                        return mac.simplify_repl; # too bad, keep the percent signs as they are...
                return mac.simplify_repl
            if mac.discard:
                return ""
            a = node.nodeargs;
            if (node.nodeoptarg):
                a.prepend(node.nodeoptarg)
            return "".join([self.node_to_text(n) for n in a])

        if (node.isNodeType(latexwalker.LatexEnvironmentNode)):
            # get environment behavior definition.
            envname = node.envname.rstrip('*');
            if (envname in self.env_dict):
                envdef = self.env_dict[envname]
            else:
                # no predefined behavior, use default:
                envdef = self.env_dict['']
            if envdef.simplify_repl:
                if (callable(envdef.simplify_repl)):
                    return envdef.simplify_repl(node)
                if ('%' in envdef.simplify_repl):
                    return envdef.simplify_repl % ("".join([self.node_to_text(nn) for nn in node.nodelist]))
                return envdef.simplify_repl
            if envdef.discard:
                return ""
            return "".join([self.node_to_text(n) for n in node.nodelist])

        if (node.isNodeType(latexwalker.LatexMathNode)):
            # if we have a math node, this means we care about math modes and we should keep this verbatim.
            return latexwalker.math_node_to_latex(node);

        logger.warning("LatexNodes2Text.node_to_text(): Unknown node: %r", node)

        # discard anything else.
        return ""









# ------------------------------------------------------------------------------






def latex2text(content, tolerant_parsing=False, keep_inline_math=False, keep_comments=False):
    """
    Extracts text from `content` meant for database indexing. `content` is
    some LaTeX code.

    .. deprecated:: 1.0
       Please use :py:class:`LatexNodes2Text` instead.
    """

    (nodelist, tpos, tlen) = latexwalker.get_latex_nodes(content, keep_inline_math=keep_inline_math,
                                                         tolerant_parsing=tolerant_parsing);

    return latexnodes2text(nodelist, keep_inline_math=keep_inline_math, keep_comments=keep_comments);


def latexnodes2text(nodelist, keep_inline_math=False, keep_comments=False):
    """
    Extracts text from a node list. `nodelist` is a list of nodes as returned by
    `latexwalker.get_latex_nodes()`.

    .. deprecated:: 1.0
       Please use :py:class:`LatexNodes2Text` instead.
    """

    return LatexNodes2Text(keep_inline_math=keep_inline_math, keep_comments=keep_comments).nodelist_to_text(nodelist)







if __name__ == '__main__':

    try:

        #latex = '\\textit{hi there!} This is {\em an equation}: \\begin{equation}\n a + bi = 0\n\\end{equation}\n\nwhere $i$ is the imaginary unit.\n';

        import fileinput

        print("Please type some latex text (Ctrl+D twice to stop) ...")

        latex = ''
        for line in fileinput.input():
            latex += line;


        print('\n--- WORDS ---\n')
        print(latex2text(latex.decode('utf-8')#, keep_inline_math=True
                         ).encode('utf-8'))
        print('\n-------------\n')

    except:
        import pdb;
        import traceback;
        import sys;
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        
        print("\nEXCEPTION: " + str(sys.exc_info()[1]) + "\n")
        
        pdb.post_mortem()


