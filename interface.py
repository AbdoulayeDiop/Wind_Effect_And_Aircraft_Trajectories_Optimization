import arbre_oaci
import wind
import new_items
import travel
import geometry
from ui_interface import Ui_Interface
from PyQt5 import QtCore, QtGui, QtWidgets
import math

ERROR_1 = "Fichier incorect. Veillez selectionner à nouveau"
ERROR_2 = "Pas de chemin trouvé. Essayez de modifier les données  entrées"
ERROR_3 = "Une erreur est survenue. Vérifiez les données entrées"
VIEW_WIDTH = 600


class ErrorWidget(QtWidgets.QDialog):
    def __init__(self, ihm, mes):
        super().__init__(ihm)
        self.vlayout = QtWidgets.QVBoxLayout(self)
        self.setWindowTitle("Message d'erreur")
        message = QtWidgets.QLabel()
        message.setText(mes)
        button = QtWidgets.QPushButton("OK")
        button.setMaximumSize(100, 20)
        button.clicked.connect(self.close)
        self.vlayout.addWidget(message)
        self.vlayout.addWidget(button, alignment=QtCore.Qt.AlignRight)


class PanZoomView(QtWidgets.QGraphicsView):
    """An interactive view that supports Pan and Zoom functions"""

    def __init__(self, scene):
        super().__init__(scene)
        # enable anti-aliasing
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        # enable drag and drop of the view
        # self.setDragMode(self.ScrollHandDrag)

    def wheelEvent(self, event):
        """Overrides method in QGraphicsView in order to zoom it when mouse scroll occurs"""
        factor = math.pow(1.001, event.angleDelta().y())
        self.zoom_view(factor)

    @QtCore.pyqtSlot(int)
    def zoom_view(self, factor):
        """Updates the zoom factor of the view"""
        self.setTransformationAnchor(self.AnchorUnderMouse)
        super().scale(factor, factor)


class IHM(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Interface()
        self.ui.setupUi(self)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("white")))
        self.view = PanZoomView(self.scene)
        self.view.setEnabled(True)
        self.view_width = VIEW_WIDTH
        self.view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.view.setObjectName("Carte")
        self.view.setScene(self.scene)
        view_layout = QtWidgets.QVBoxLayout(self.ui.carte)
        view_layout.addWidget(self.view)
        self.log_Layout = QtWidgets.QVBoxLayout(self.ui.log)
        self.table = None
        self.m = None
        self.graph = None
        self.graph_dim = None
        self.wind3D_dict = None
        self.aeronef_dict = None
        self.path_Group = None
        self.nodes_Group = None
        self.windPlanItem = None
        self.rose = new_items.RoseDesVents(self.scene)

        self.ui.pushButton_calculer.setToolTip("Calculer la trajectoire optimale")
        self.ui.pushButton_save.setToolTip("Sauvegarder les résultats")

        self.ui.pushButton_a.clicked.connect(self.load_nodes)
        self.ui.pushButton_v.clicked.connect(self.load_winds)
        self.ui.pushButton_ae.clicked.connect(self.load_aeronef)
        self.ui.pushButton_calculer.clicked.connect(self.search)
        self.ui.pushButton_save.clicked.connect(self.save_data)
        self.ui.dial.valueChanged.connect(self.add_windPlan)
        self.ui.comboBox_ae.currentTextChanged.connect(self.add_aeronef)

        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap("./ressources/icon")))

    # Charger les différents fichiers___________________________________________________________________________________
    def load_nodes(self):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Charger les aérodromes", "", "Text Files (*.txt)",
                                                            options=options)
        if filename:
            try:
                self.graph = arbre_oaci.arbre_creation(filename)
                self.graph_dim = self.graph.dim()
                self.add_nodes()
                self.m = geometry.find_latmoy(filename)
                self.ui.pushButton_v.setEnabled(True)
            except Exception:
                error_window = ErrorWidget(self, ERROR_1)
                error_window.show()

    def load_winds(self):
        options = QtWidgets.QFileDialog.Options()
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Charger les aérodromes", "", "Text Files (*.txt)",
                                                          options=options)
        if files:
            try:
                self.wind3D_dict = wind.create_wind3D_dict(files, self.m)
                pression_min = int(min(list(self.wind3D_dict.values())[0].dict))
                pression_max = int(max(list(self.wind3D_dict.values())[0].dict))
                self.ui.dial.setMinimum(pression_min)
                self.ui.dial.setMaximum(pression_max)
                self.ui.dial.setEnabled(True)
                self.ui.pushButton_calculer.setEnabled(True)
                self.add_windPlan()
                self.ui.timeEdit.timeChanged.connect(self.add_windPlan)
            except Exception:
                error_window = ErrorWidget(self, ERROR_1)
                error_window.show()

    def load_aeronef(self):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Charger les aérodromes", "", "Text Files (*.txt)",
                                                            options=options)
        if filename:
            try:
                self.aeronef_dict = travel.from_file(filename)
                for id, airplane in self.aeronef_dict.items():
                    if self.ui.comboBox_ae.findText(id) == -1:
                        self.ui.comboBox_ae.addItem(id)
            except Exception:
                error_window = ErrorWidget(self, ERROR_1)
                error_window.show()

    # __________________________________________________________________________________________________________________

    # Ajouter les données chargées______________________________________________________________________________________
    def add_nodes(self):
        if self.nodes_Group:
            self.scene.removeItem(self.nodes_Group)
            if self.path_Group:
                self.scene.removeItem(self.path_Group)
        self.nodes_Group = QtWidgets.QGraphicsItemGroup()
        for id, node in self.graph.nodes_dict.items():
            if self.ui.comboBox_depart.findText(id) == -1:
                self.ui.comboBox_depart.addItem(id)
            if self.ui.comboBox_arrive.findText(id) == -1:
                self.ui.comboBox_arrive.addItem(id)
            item = new_items.NodeItems(self, node)
            self.nodes_Group.addToGroup(item)
            self.scene.addItem(self.nodes_Group)
        self.rose.draw()

    def add_windPlan(self):
        wind3D = arbre_oaci.get_wind3D(self.wind3D_dict, arbre_oaci.time(self.ui.timeEdit.text()))
        (alt, windPlan) = min(wind3D.dict.items(), key=lambda x: abs(x[0] - self.ui.dial.value()))
        if self.windPlanItem:
            self.scene.removeItem(self.windPlanItem)
        self.windPlanItem = new_items.WindPlanItems(self, windPlan)
        self.scene.addItem(self.windPlanItem)

    def add_aeronef(self):
        id = self.ui.comboBox_ae.currentText()
        aeronef = self.aeronef_dict[id]
        self.ui.spinBox_pression_inf.setValue(aeronef.pression_inf)
        self.ui.spinBox_pression_sup.setValue(aeronef.pression_sup)
        self.ui.spinBox_vitesse.setValue(aeronef.v_c)
        self.ui.spinBox_tempsdarret.setValue(aeronef.X)

    # __________________________________________________________________________________________________________________


    # Création du Pseudo-log de navigation______________________________________________________________________________
    def add_edge(self, edge, table, i):
        duration = QtWidgets.QLabel(str(int(edge.duration * 1e2) / 1e2) + " s = " + arbre_oaci.hms(edge.duration))
        wind = QtWidgets.QLabel(str(int(abs(edge.windvect) * 3600 / 1852 * 1e2) / 1e2))
        windangle = QtWidgets.QLabel(str(int(edge.windangle * 180 / math.pi * 1e2) / 1e2))
        deviation = QtWidgets.QLabel(str(int(edge.deviation * 180 / math.pi * 1e2) / 1e2))
        grounspeed = QtWidgets.QLabel(str(int(edge.groundspeed * 1e2) / 1e2))
        table.setCellWidget(i, 1, wind)
        table.setCellWidget(i, 2, windangle)
        table.setCellWidget(i, 3, deviation)
        table.setCellWidget(i, 4, grounspeed)
        table.setCellWidget(i, 5, duration)

    def create_log(self):
        if self.table:
            self.log_Layout.removeWidget(self.table)
        self.table = QtWidgets.QTableWidget(1 + len(self.flight1.edges), 6)
        self.table.setCellWidget(0, 0, QtWidgets.QLabel("Trajet"))
        self.table.setCellWidget(0, 1, QtWidgets.QLabel("Vent (kt)"))
        self.table.setCellWidget(0, 2, QtWidgets.QLabel("Angle au vent (°)"))
        self.table.setCellWidget(0, 3, QtWidgets.QLabel("Déviation (°)"))
        self.table.setCellWidget(0, 4, QtWidgets.QLabel("Vitesse/sol (m/s)"))
        self.table.setCellWidget(0, 5, QtWidgets.QLabel("Durée"))
        for (i, edge) in enumerate(self.flight1.edges):
            label = QtWidgets.QLabel(edge.dep.id + " -> " + edge.arr.id)
            self.table.setCellWidget(i + 1, 0, label)
            self.add_edge(edge, self.table, i + 1)
        self.log_Layout.addWidget(self.table)

    # __________________________________________________________________________________________________________________

    def draw_path(self, flight, color, path_width, node_width):
        """
        :param flight: travel.Flight
        :param color: str
        :param path_width: int
        :param node_width: int
        trace la trajectoire avec un QPainterPath
        """
        pen = QtGui.QPen(QtGui.QColor(color), path_width)
        painter = QtGui.QPainterPath()
        w = node_width / 2
        a = flight.dep.coord.adapt_scale(self.view_width, self.graph_dim)
        painter.moveTo(a.x + w, a.y + w)
        for k in range(len(flight.path) - 1):
            b = self.graph.nodes_dict[flight.path[k + 1]].coord.adapt_scale(self.view_width, self.graph_dim)
            painter.lineTo(b.x + w, b.y + w)
        item = QtWidgets.QGraphicsPathItem(painter, self.path_Group)
        item.setPen(pen)
        item.setToolTip("Trajectoire avec vent") if node_width >= 8 else item.setToolTip("Trajectoire sans vent")
        for id in flight.path:
            b = self.graph.nodes_dict[id].coord.adapt_scale(self.view_width, self.graph_dim)
            item2 = QtWidgets.QGraphicsEllipseItem(b.x, b.y, node_width, node_width, self.path_Group)
            item2.setBrush(QtGui.QBrush(QtGui.QColor("#FF1B1C")))
            item2.setToolTip(id)
        self.scene.addItem(self.path_Group)

    def reinitialize(self, graph):
        """
        :param graph: arbre_oaci.Graph
        réinitialise le graphe graph
        """
        for (id, node) in graph.nodes_dict.items():
            node.parent, node.H, node.G = None, 0, 0

    def search(self):
        """
        calcul et affichage de la trajectoire optimale et du Pseudo-log de navigation
        """
        if self.path_Group:
            self.scene.removeItem(self.path_Group)
        self.path_Group = QtWidgets.QGraphicsItemGroup()
        while range(self.ui.listWidget.count()):
            self.ui.listWidget.takeItem(0)
        try:
            dep = self.graph.nodes_dict[self.ui.comboBox_depart.currentText()]
            arr = self.graph.nodes_dict[self.ui.comboBox_arrive.currentText()]
            timeStart = self.ui.timeEdit.text()
            v_c = self.ui.spinBox_vitesse.value()
            pression_inf = self.ui.spinBox_pression_inf.value()
            pression_sup = self.ui.spinBox_pression_sup.value()
            temps_arret = self.ui.spinBox_tempsdarret.value() * 60
            airplane = travel.Airplane(pression_inf, pression_sup, temps_arret, v_c)
            self.reinitialize(self.graph)
            self.flight1 = arbre_oaci.find_path(dep, arr, timeStart, airplane, self.graph, self.wind3D_dict)
            self.reinitialize(self.graph)
            flight2 = arbre_oaci.find_path(dep, arr, timeStart, airplane, self.graph)
            self.draw_path(flight2, "#FF7F11", 1, 6)
            self.draw_path(self.flight1, "#FF1B1C", 3, 8)
            self.rose.draw(self.rose.get_dir(dep.coord, arr.coord))
            self.ui.dial.setValue(self.flight1.pression)
            self.ui.lineEdit_1.setText(str(arbre_oaci.hms(self.flight1.duration)))
            self.ui.lineEdit_2.setText(str(arbre_oaci.hms(flight2.duration)))
            self.ui.lineEdit_3.setText(str(self.flight1.pression) + " hPa")
            self.create_log()
            self.ui.pushButton_save.setEnabled(True)
        except arbre_oaci.NoPathError:
            error_window = ErrorWidget(self, ERROR_2)
            error_window.show()
        except Exception:
            error_window = ErrorWidget(self, ERROR_3)
            error_window.show()

    def save_data(self):
        """
        sauvegarde la recherche dans l'historique
        """
        options = QtWidgets.QFileDialog.Options()
        file, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Charger les aérodromes", "", "Text Files (*.txt)",
                                                        options=options)
        if file:
            with open(file, "a") as f:
                f.write("\nDepart            : " + str(self.flight1.dep.id))
                f.write("\nArrive            : " + str(self.flight1.arr.id))
                f.write("\nHeure de depart   : " + str(arbre_oaci.hms(self.flight1.time_start)))
                f.write("\nChemin optimal    : " + str(self.flight1.path))
                f.write("\nduree minimale    = " + str(self.flight1.duration) + " sec")
                f.write("\npression optimale = " + str(self.flight1.pression) + " hPa\n")
