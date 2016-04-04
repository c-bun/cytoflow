#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from traits.api import HasTraits, List, Instance, on_trait_change
from traitsui.api import View, Item

from cytoflowgui.vertical_notebook_editor import VerticalNotebookEditor
from cytoflowgui.workflow_item import WorkflowItem

# threading AND multiprocessing, oh my!

import multiprocessing
import threading

class Workflow(HasTraits):
    """
    A list of WorkflowItems.
    """

    workflow = List(WorkflowItem)
    selected = Instance(WorkflowItem)

    traits_view = View(Item(name='workflow',
                            id='table',
                            editor=VerticalNotebookEditor(page_name='.name',
                                                          page_description='.friendly_id',
                                                          page_icon='.icon',
                                                          selected = 'selected',
                                                          scrollable = True,
                                                          multiple_open = False,
                                                          delete = True),
                            show_label = False
                            ),
                       #resizable = True
                       )
    
    # multiprocessing and multithreading plan:
    # each time 
    
    @on_trait_change('workflow[]')
    def _on_workflow_changed(self, name, removed, added):
        pass
    
    conn = Any
    model = List(WorkflowItem)
    
    def wait_for_updates(self):
        while True:
            (pos, items) = self.conn.recv()
            del self.workflow[pos:]
            self.workflow[-1].next = items[0]
            items[0].previous = self.workflow[-1]
            self.workflow.extend(items)    
            
            
from util import UniquePriorityQueue

def start_worker_process(conn):
    p = WorkflowManager(conn = conn)
    p.wait_for_updates()
    
    