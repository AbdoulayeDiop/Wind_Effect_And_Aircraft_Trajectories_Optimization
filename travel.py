import geometry
from numpy import cos, sin, pi


class Flight():
    """represente le vol entre 2 aerodromes données
        -dep: Node aerodrome de départ
        -arr: Node aerodrome d'arrivé
        -pression: int pression du vol considéré
        -time_start: float heure de départ en secondes
        -duration: float durée du trajet
        -path: list liste des id des aerodromes suivis
        -edges: list(arbre_oaci.Edge) liste des trajets intermédiaires"""

    def __init__(self, dep, arr, pression, time_start):
        self.dep = dep
        self.arr = arr
        self.pression = pression
        self.time_start = time_start
        self.duration = None
        self.path = None
        self.edges = []

    def __repr__(self):
        return "flight : pression = {0.pression} hPa ; ".format(self) + "duration = " + str(
            self.duration) + " ; path = {0.path}".format(self)


class Airplane:
    """represente un avion
        -pression_inf: int pression minimale à laquelle l'avion peut voler
        -pression_sup: int pression maximale à laquelle l'avion peut voler
        -v_c: float vitesse de croisière de l'avion
        -X: int temps d'arrêt de l'avion"""

    def __init__(self, pression_inf, pression_sup, X, vitesse_croisiere):
        self.pression_inf = pression_inf
        self.pression_sup = pression_sup
        self.v_c = vitesse_croisiere
        self.X = X


def from_file(filename):
    airplane_dict = {}
    with open(filename, "r") as f:
        for line in f:
            l = line.strip().split()
            airplane = Airplane(int(l[1]), int(l[2]), int(l[3]), int(l[4]))
            airplane_dict[l[0]] = airplane
    return airplane_dict
