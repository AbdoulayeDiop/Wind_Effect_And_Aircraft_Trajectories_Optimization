from PyQt5 import QtGui, QtWidgets
import numpy as np


class RoseDesVents(QtWidgets.QGraphicsItemGroup):
    def __init__(self, scene, p0=np.array([50, 550])):
        super().__init__()
        self.scene = scene
        self.p0 = p0
        self.roseItem = None
        self.dirItem = None

        def produit(x, A):
            n = len(x)
            y = np.zeros(n)
            for j in range(n):
                yj = 0
                for i in range(n):
                    yj += x[i] * A[i][j]
                y[j] = yj
            return y

        A = np.array([[0, 1], [-1, 0]])
        po = np.array([-40, 0])
        pno = np.array([-5, -5])
        self.l = [po, pno]
        for i in range(3):
            po = produit(po, A)
            self.l.append(po)
            pno = produit(pno, A)
            self.l.append(pno)

    def draw(self, dir=None):
        painter = QtGui.QPainterPath()
        if dir == None:
            if self.roseItem:
                self.scene.removeItem(self.roseItem)
            if self.dirItem:
                self.scene.removeItem(self.dirItem)
            painter.moveTo((self.l[0] + self.p0)[0], (self.l[0] + self.p0)[1])
            pen = QtGui.QPen(QtGui.QColor("black"), 2)
            for i in range(1, len(self.l)):
                painter.lineTo((self.l[i] + self.p0)[0], (self.l[i] + self.p0)[1])
            painter.lineTo((self.l[0] + self.p0)[0], (self.l[0] + self.p0)[1])
            painter.moveTo((self.l[1] + self.p0)[0], (self.l[1] + self.p0)[1])
            painter.lineTo((self.l[5] + self.p0)[0], (self.l[5] + self.p0)[1])
            painter.moveTo((self.l[3] + self.p0)[0], (self.l[3] + self.p0)[1])
            painter.lineTo((self.l[7] + self.p0)[0], (self.l[7] + self.p0)[1])
            self.roseItem = QtWidgets.QGraphicsPathItem(painter, self)
            self.roseItem.setPen(pen)
            self.roseItem.setToolTip("Rose des vents")
            self.scene.addItem(self.roseItem)
        else:
            if self.dirItem:
                self.scene.removeItem(self.dirItem)
            pen = QtGui.QPen(QtGui.QColor("#FF1B1C"), 4)
            painter.moveTo(self.p0[0], self.p0[1])
            for i in range(-1, 2):
                painter.lineTo((self.l[dir + i] + self.p0)[0], (self.l[dir + i] + self.p0)[1])
            painter.lineTo(self.p0[0], self.p0[1])
            self.dirItem = QtWidgets.QGraphicsPathItem(painter, self)
            self.dirItem.setPen(pen)
            self.dirItem.setToolTip("sens du trajet")
            self.scene.addItem(self.dirItem)

    def get_dir(self, a, b):
        if a == b:
            return None
        else:
            ab = b - a
            if abs(ab.x) - abs(ab.y) >= 0:
                return 4 if ab.x > 0 else 0
            else:
                return 2 if ab.y > 0 else 6


class NodeItems(QtWidgets.QGraphicsItemGroup):
    def __init__(self, ihm, node):
        super().__init__()
        self.ihm = ihm
        self.node = node
        a = self.node.coord.adapt_scale(self.ihm.view_width, self.ihm.graph_dim)
        self.nodeItem = QtWidgets.QGraphicsEllipseItem(a.x, a.y, 5, 5, self)
        self.nodeItem.setBrush(QtGui.QBrush(QtGui.QColor("black")))
        self.nodeItem.setToolTip(self.node.id)


class WindLocalItems(QtWidgets.QGraphicsItemGroup):
    def __init__(self, ihm, windlocal):
        super().__init__()
        self.ihm = ihm
        self.windlocal = windlocal
        pen = QtGui.QPen(QtGui.QColor("#989898"), 1)
        vectPainter = QtGui.QPainterPath()
        p1 = int(self.windlocal.coord.adapt_scale(self.ihm.view_width, self.ihm.graph_dim).x), int(
            self.windlocal.coord.adapt_scale(self.ihm.view_width, self.ihm.graph_dim).y)
        p2 = int(p1[0] + self.windlocal.u), int(p1[1] - self.windlocal.v)
        vectPainter.addEllipse(p1[0], p1[1], 2, 2)
        vectPainter.moveTo(p1[0] + 1, p1[1] + 1)
        vectPainter.lineTo(p2[0] + 1, p2[1] + 1)
        self.vectItem = QtWidgets.QGraphicsPathItem(vectPainter, self)
        self.vectItem.setPen(pen)


class WindPlanItems(QtWidgets.QGraphicsItemGroup):
    def __init__(self, ihm, windPlan):
        super().__init__()
        self.ihm = ihm
        self.windPlan = windPlan
        for wind in self.windPlan.dict.values():
            self.addToGroup(WindLocalItems(self.ihm, wind))
