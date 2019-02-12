import sys
from PyQt5.QtWidgets import QApplication
from interface import IHM

app = QApplication(sys.argv)
my_IHM = IHM()
my_IHM.showMaximized()
sys.exit(app.exec_())
