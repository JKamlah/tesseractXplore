from kivy.uix.filechooser import FileChooserListView

class MyFileChooser(FileChooserListView):
    '''Class implementing content for a tab.'''

    def entry_released(self, entry, touch):
        '''(internal) This method must be called by the template when an entry
        is touched by the user.

        .. versionadded:: 1.1.0
        '''
        if (
            'button' in touch.profile and touch.button in (
                'scrollup', 'scrolldown', 'scrollleft', 'scrollright')):
            return False
        # TODO: This line is preventing multiselect from loading single objects
        #if not self.multiselect:
        if self.file_system.is_dir(entry.path) and not self.dirselect:
            self.open_entry(entry)
        elif touch.is_double_tap:
            if self.dirselect and self.file_system.is_dir(entry.path):
                return
            else:
                self.selection.append(entry.path)
                self.dispatch('on_submit', self.selection, touch)

    def _update_item_selection(self, *args):
        for item in self._items:
            item.selected = item.path in self.selection
            # TODO: This var is missing in the current version, issue is made (https://github.com/kivy/kivy/issues/7554)
            item.is_selected = item.path in self.selection



