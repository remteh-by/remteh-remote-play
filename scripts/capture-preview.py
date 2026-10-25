#!/usr/bin/env python3
"""Capture the real Qt setup UI in isolated temporary storage; no owner data."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
import sys,tempfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'desktop/linux'))
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase
import launcher,controller,update_ui
app=QApplication([]);app.setStyleSheet(launcher.STYLE)
QFontDatabase.addApplicationFont(str(ROOT/'desktop/linux/assets/fonts/IBMPlexSans.ttf'))
with tempfile.TemporaryDirectory() as directory:
 root=Path(directory)
 with patch.object(launcher,'DATA',root/'data'),patch.object(launcher,'PRIVATE',root/'private'),patch.object(launcher,'CONFIG',root/'private/preferences.json'),patch.object(launcher.Deckivo,'refresh',lambda self:None),patch.object(launcher,'ControllerMonitor',controller.ControllerMonitor),patch.object(update_ui,'initialize',lambda self:None):
  window=launcher.Deckivo();window.resize(1280,720);window.show();app.processEvents()
  window.grab().save(str(ROOT/'build/deckivo-ui.png'))
  window.close();app.processEvents()
