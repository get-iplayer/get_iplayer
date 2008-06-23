# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# a simple plugin to run arbitrary iplayer from a directory.
# it determines success or failure of iplayer based on its exit status.
# -----------------------------------------------------------------------
# $Id: iplayer.py 10719 2008-06-22 02:36:13Z plewis $
#
# Notes: no echo of output of iplayer to screen.
#        To use add the following to local_conf.py:
#        plugin.activate('iplayer', level=45)
#        IPLAYER_DIR = '/usr/local/freevo_data/Iplayer'
# Todo: find a way to prompt for arguments. interactive display of output?
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2003 Krister Lagerstrom, et al.
# Please see the file freevo/Docs/CREDITS for a complete list of authors.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------


#python modules
import os, time
import pygame

#freevo modules
import config
import menu
import plugin
import util
import childapp
import osd
import fxditem
import rc

from event import *
from item import Item
from gui.ListBox import ListBox
from gui.RegionScroller import RegionScroller
from gui.PopupBox import PopupBox


def islog(name):
    f = open(os.path.join(config.FREEVO_LOGDIR, 'iplayer-std%s-%s.log' % (name, os.getuid())))
    data = f.readline()
    if name == 'out':
        data = f.readline()
    f.close()
    return data


class IplayerChild(childapp.ChildApp2):
    def poll(self):
        pass


class IplayerItem(Item):
    """
    This is the class that actually runs the iplayer. Eventually hope to add
    actions for different ways of running iplayer and for displaying stdout
    and stderr of last iplayer run.

    @ivar display_type: 'iplayer'
    @ivar stoposd: stop the OSD, False if running under X11
    @ivar stdout: log to stdout
    @ivar rc: remote control singleton
    """
    def __init__(self, iplayer=None, directory=None):
        Item.__init__(self, skin_type='iplayer')
        self.display_type = 'iplayer'
        self.stoposd = False
        self.stdout  = True
        self.rc      = rc.get_singleton()
        if iplayer and directory:
            self.name  = iplayer
            self.cmd   = os.path.join(directory, iplayer)
            self.image = util.getimage(self.cmd)


    def actions(self):
        """
        return a list of actions for this item
        """
        return [ (self.flashpopup , _('Run iplayer')) ]


    def flashpopup(self, arg=None, menuw=None):
        """
        start popup and execute iplayer
        """

        if self.stoposd:
            self.rc.suspend()

        workapp = IplayerChild(self.cmd, 'iplayer', 1, self.stoposd)
        while workapp.isAlive():
            # make sure all callbacks in rc are running
            if not self.stoposd:
                self.rc.poll()
            # wait some time
            time.sleep(0.5)

        workapp.stop()

        if self.stoposd:
            self.rc.resume()


def fxdparser(fxd, node):
    """
    parse iplayer out of a fxd file
    """
    item = IplayerItem()
    item.name    = fxd.getattr(node, 'title')
    item.cmd     = fxd.childcontent(node, 'cmd')
    item.image   = util.getimage(item.cmd)
    if fxd.get_children(node, 'stoposd'):
        item.stoposd = True
    if fxd.get_children(node, 'nostdout'):
        item.stdout =  False

    # parse <info> tag
    fxd.parse_info(fxd.get_children(node, 'info', 1), item)
    fxd.getattr(None, 'items', []).append(item)


class IplayerMenuItem(Item):
    """
    this is the item for the main menu and creates the list
    of iplayer in a submenu.
    """
    def __init__(self, parent):
        Item.__init__(self, parent, skin_type='iplayer')
        self.name = _('Watch iplayer')


    def actions(self):
        """
        return a list of actions for this item
        """
        items = [ (self.create_iplayer_menu , 'iplayer') ]
        return items


    def create_iplayer_menu(self, arg=None, menuw=None):
        """
        create a list with iplayer
        """
        iplayer_items = []
        for iplayer in os.listdir(config.IPLAYER_DIR):
            if os.path.splitext(iplayer)[1] in ('.jpg', '.png'):
                continue
            if os.path.splitext(iplayer)[1] in ('.fxd', '.xml'):
                fxd_file=os.path.join(config.IPLAYER_DIR, iplayer)

                # create a basic fxd parser
                parser = util.fxdparser.FXD(fxd_file)

                # create items to add
                parser.setattr(None, 'items', iplayer_items)

                # set handler
                parser.set_handler('iplayer', fxdparser)

                # start the parsing
                parser.parse()
            else:
                cmd_item = IplayerItem(iplayer, config.IPLAYER_DIR)
                iplayer_items.append(cmd_item)

        iplayer_items.sort(lambda l, o: cmp(l.name.upper(), o.name.upper()))
        iplayer_menu = menu.Menu(_('Watch iplayer'), iplayer_items)
        menuw.pushmenu(iplayer_menu)
        menuw.refresh()



class PluginInterface(plugin.MainMenuPlugin):
    """
    A small plugin to run iplayer from the main menu. All output is logged in the freevo logdir, and
    success or failure is determined on the return value of the iplayer. You can now
    also view the log file after the iplayer has finished in freevo itself.

    to activate it, put the following in your local_conf.py:

    | plugin.activate('iplayer', level=45)
    | IPLAYER_DIR = '/usr/local/freevo_data/Iplayer'

    The level argument is used to influence the placement in the Main Menu. consult
    freevo_config.py for the level of the other Menu Items if you wish to place it
    in a particular location.

    This plugin also activates <iplayer> tag support in all menus, see information
    from iplayer.fxdhandler for details.
    """

    def __init__(self):
        # register iplayer to normal fxd item parser
        # to enable <iplayer> tags in fxd files in every menu
        plugin.register_callback('fxditem', [], 'iplayer', fxdparser)
        plugin.MainMenuPlugin.__init__(self)

    def items(self, parent):
        return [ IplayerMenuItem(parent) ]

    def config(self):
        return [
            ('IPLAYER_DIR', '/usr/local/bin', 'The directory to show iplayer from.'),
        ]


class fxdhandler(plugin.Plugin):
    """
    Small plugin to enable <iplayer> tags inside fxd files in every menu. You
    don't need this plugin if you activate the complete 'iplayer' plugin.

    to activate it, put the following in your local_conf.py:
    plugin.activate('iplayer.fxdhandler')

    Sample fxd file starting mozilla::

        <?xml version="1.0" ?>
        <freevo>
          <iplayer title="Mozilla">
            <cmd>/usr/local/bin/mozilla</cmd>
            <stoposd />  <!-- stop osd before starting -->
            <nostdout /> <!-- do not show stdout on exit -->
            <info>
              <description>Unleash mozilla on the www</description>
            </info>
          </iplayer>
        </freevo>

    Putting a <iplayer> in a folder.fxd will add this iplayer to the list of
    item actions for that directory.
    """
    def __init__(self):
        # register iplayer to normal fxd item parser
        # to enable <iplayer> tags in fxd files in every menu
        plugin.register_callback('fxditem', [], 'iplayer', fxdparser)
        plugin.Plugin.__init__(self)



class IplayerMainMenuItem(plugin.MainMenuPlugin):
    """
    A small plugin to put a iplayer in the main menu.
    Uses the iplayer.py fxd file format to say which iplayer to run.
    All output is logged in the freevo logdir.
    to activate it, put the following in your local_conf.py:

    | plugin.activate('iplayer.IplayerMainMenuItem', args=(/usr/local/freevo_data/Iplayer/Mozilla.fxd',), level=45)

    The level argument is used to influence the placement in the Main Menu.
    consult freevo_config.py for the level of the other Menu Items if you
    wish to place it in a particular location.
    """
    def __init__(self, iplayerxmlfile):
        plugin.MainMenuPlugin.__init__(self)
        self.cmd_xml = iplayerxmlfile


    def config(self):
        return [ ]


    def items(self, parent):
        iplayer_items = []
        parser = util.fxdparser.FXD(self.cmd_xml)
        parser.setattr(None, 'items', iplayer_items)
        parser.set_handler('iplayer', fxdparser)
        parser.parse()
        cmd_item = iplayer_items[0]
        return [ cmd_item ]
