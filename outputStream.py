# -*- coding: utf-8 -*-
"""Contains the class OutputStream, a HasTraits file-like text buffer.
This was taken from the internet. It essentially acts like a text box 
that always scrolls to the last position which is exactly what we want. 
We don't need the pause functionality. 

Added a method called addLine that also writes to the log file.

All lines start with >>>

Note that the coding at the top of this page is actually important as
German windows can sometimes print ü etc. in error messages....

"""

from traits.api import HasTraits, Str, Bool, Trait, Int
from traitsui.api import View, UItem, TextEditor, Handler
from traits.etsconfig.api import ETSConfig
from traitsui.qt4.text_editor import CustomEditor

import logging

logger=logging.getLogger("ExperimentSnake.outputStream")

DEFAULT_MAX_LEN = 8000

try:
    import labSounds
    ss=labSounds.getSoundSystem()
except ImportError as e:
    print "no winsound module found... I won't be able to speak :("
    ss=None


def update_editor_html ( self ):
    """ 
    Here we create a new update_editor function so that we can can use html to
    make the formatting nice.
    Updates the editor when the object trait changes externally to the
        editor.
    """
    user_value = self._get_user_value()
    try:
        unequal = bool(user_value != self.value)
    except ValueError:
        # This might be a numpy array.
        unequal = True

    if unequal:
        self._no_update = True
        self.control.setHtml(self.str_value)
        self._no_update = False

    if self._error is not None:
        self._error = None
        self.ui.errors -= 1
        self.set_error_state( False )

CustomEditor.update_editor = update_editor_html


class _OutputStreamViewHandler(Handler):
    
    def init(self, uiinfo):
        """called when view constructed """
        super(_OutputStreamViewHandler,self).init(uiinfo)
        ui = uiinfo.ui
        if ui is None:
            return

        for ed in  ui._editors:
            logger.debug("init--> editor %s" % ed)
            if ed.name == 'text':
                logger.debug("init-->text editor %s" % ed)
                logger.debug("init-->type text editor %s" % type(ed))
                break
        else:
            # Did not find an editor with the name 'text'.
            return
            
        #override the method of an instance
        # in this case we are overriding such that the update editor calls an html insert not plain text
        #this allows the output stream to have much nicer formatting
        logger.debug("customEditor %s" % CustomEditor.update_editor)
        logger.debug("type customEditor %s" % type(CustomEditor.update_editor))

        
    def object_text_changed(self, uiinfo):
        ui = uiinfo.ui
        if ui is None:
            return

        for ed in  ui._editors:
            logger.debug("editor %s" % ed)
            if ed.name == 'text':
                logger.debug("text editor %s" % ed)
                logger.debug("type text editor %s" % type(ed))
                break
        else:
            # Did not find an editor with the name 'text'.
            return

        if ETSConfig.toolkit == 'wx':
            # With wx, the control is a TextCtrl instance.
            ed.control.SetInsertionPointEnd()
        elif ETSConfig.toolkit == 'qt4':
            # With qt4, the control is a PyQt4.QtGui.QTextEdit instance.
            from PyQt4.QtGui import QTextCursor
            ed.control.moveCursor(QTextCursor.End)
            


class OutputStream(HasTraits):
    """This class has methods to emulate an file-like output string buffer.
    
    It has a default View that shows a multiline TextEditor.  The view will
    automatically move to the end of the displayed text when data is written
    using the write() method.
    
    The `max_len` attribute specifies the maximum number of bytes saved by
    the object.  `max_len` may be set to None.
    
    The `paused` attribute is a bool; when True, text written to the
    OutputStream is saved in a separate buffer, and the display (if there is
    one) does not update.  When `paused` returns is set to False, the data is
    copied from the paused buffer to the main text string. 
    """
    
    # The text that has been written with the 'write' method.
    text = Str

    # The maximum allowed length of self.text (and self._paused_buffer).
    max_len = Trait(DEFAULT_MAX_LEN, None, Int)

    # When True, the 'write' method appends its value to self._paused_buffer
    # instead of self.text.  When the value changes from True to False,
    # self._paused_buffer is copied back to self.text.
    paused = Bool(False)
    
    # String that holds text written while self.paused is True.
    _paused_buffer = Str
    
    #format Codes 0 standard, 1 bold, 2 red 
    formatCode =  Int
    tabString = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    def write(self, s):
        if self.paused:
            self._paused_buffer = self._truncated_concat(self._paused_buffer, s)
        else:
            self.text = self._truncated_concat(self.text, s)
            
    def addLine(self, s, formatCode = 0):
        """add a line in the format that we want for experiment snake and log the line
        with info level. Can always filter to these using ">>>" to search

        format codes (could use a string for clarity?)        
        0= normal black font, no emphasis etc.
        1 = black font & bold
        2=  normal black font, no bold with indent
        3 = red font and bold
        4 = red font and bold with indent
        
        
        """
        self.formatCode = formatCode
        #We may need to handle the fact that German windows using non ascii characters!
        #This is a nightmare and should be avoided but sometimes I print socket errors which have  "ü" etc...
        s=s.decode("utf-8")

        if len(s)>0:
            #self.write(">>> %s\n"% s)
            if formatCode ==0:
                self.write(">>> %s <br>"% s)
            elif formatCode ==1:
                self.write(">>> <b>%s</b><br>"% s)
            elif formatCode ==2:
                self.write("%s>>>%s<br>"% (self.tabString,s))
            elif formatCode ==3:
                self.write('<font color="red"><b>>>>%s<br></b></font>'% s)
                if ss is not None:
                    ss.againstMyWishes(1)
            elif formatCode ==4:
                self.write('%s<font color="red"><b>>>>%s<br></b></font>'% (self.tabString,s))
                if ss is not None:
                    ss.againstMyWishes(1)
            logger.info(">>> %s" % s)               

    def flush(self):
        pass

    def close(self):
        pass

    def reset(self):
        self._paused_buffer = ''
        self.paused = False
        self.text = ''

    def _truncated_concat(self, text, s):
        if len(s) >= self.max_len:
            # s could be huge. Handle this case separately, to avoid the temporary
            # created by 'text + s'.
            result = s[-self.max_len:]
        else:
            result = (text + s)[-self.max_len:]
        return result

    def _paused_changed(self):
        if self.paused:
            # Copy the current text to _paused_buffer.  While the OutputStream
            # is paused, the write() method will append its argument to _paused_buffer.
            self._paused_buffer = self.text
        else:
            # No longer paused, so copy the _paused_buffer to the displayed text, and
            # reset _paused_buffer.
            self.text = self._paused_buffer
            self._paused_buffer = ''

    def traits_view(self):
        view = \
            View(
                UItem('text', editor=TextEditor(multi_line=True), style='custom'),
                handler=_OutputStreamViewHandler(),
            )
        return view
        
if __name__=="__main__":
    
    ops = OutputStream()
    ops.addLine("test")
    ops.addLine("test2",2)
    ops.addLine("Bitte überprüfen",2)
    ops.configure_traits()
    
    