import geometry
import travel
from numpy import cos, sin, pi


class Graph():
    """représente l'ensemble des aérodromes
    - nodes_dict: dict dictionnaire contenant les noeuds ou aerodromes
    - parent_edge: dict dictionnaire contenant les edges reliant chaque noeud à son parent
    """

    def __init__(self):
        self.nodes_dict = {}
        self.parent_edge = {}

    def add(self, node):
        self.nodes_dict[node.id] = node

    def remove(self, node):
        self.nodes_dict.pop(node)

    def __repr__(self):
        return "<Graph {0.nodes_dict}>".format(self)

    def dim(self):
        min_x = min(node.coord.x for node in self.nodes_dict.values())
        max_x = max(node.coord.x for node in self.nodes_dict.values())
        min_y = min(node.coord.y for node in self.nodes_dict.values())
        max_y = max(node.coord.y for node in self.nodes_dict.values())
        return min_x, max_x, min_y, max_y


class Node():
    """represente un aedrome dans le graphe
        - id: string code OACI
        - coord: geometry.Point coordonnées de l'aerodrome
        - parent: Node parent du noeud considéré
        - H: float heuristique(estimation de la durée vers l'arrivé) du noeud courant
        - G: float durée du trajet depuis le départ"""

    def __init__(self, id_oaci, coord):
        self.id = id_oaci
        self.coord = coord
        self.parent = None
        self.H = 0
        self.G = 0

    def __repr__(self):
        return "<Node {0.id}: {0.coord}>".format(self)

    def voisins(self, airplane, graphe, windPlan):
        """voisin(Node, travel.Airplane, Graph, wind.WindPlan) return dict
        renvoie le dictionnaire des voisins à moin de X min"""
        dico = {}
        for (id, node) in graphe.nodes_dict.items():
            if id != self.id:
                edge = Edge(self, node)
                edge.calcul(airplane, windPlan=windPlan)
                if edge.duration <= airplane.X:
                    dico[id] = edge
        return dico


class Edge():
    """
    représente le trajet direct entre 2 aerodomes
    -dep: Node aerodrome de départ
    -arr: Node aerodrome d'arrivé
    -duration: float durée du trajet
    -windvect: geometry.Vect vent moyen entre dep et arr
    -windangle: float angle au vent (en rad)
    -déviation: float angle de déviation dû au vent (en rad)
    -groundspeed: float vitesse par rapport au sol
    """

    def __init__(self, dep, arr):
        self.dep = dep
        self.arr = arr
        self.duration = None
        self.windvect = None
        self.windangle = None
        self.deviation = None
        self.groundspeed = None

    def calcul(self, airplane, windPlan=None):
        """
        :param airplane: travel.Airplane aeronef utilisé
        :param windPlan: wind.WindPlan ensemble des vent sur une isobare donnée
        calcule les attributs de self
        """
        ab_vect = geometry.Vect(self.arr.coord.x - self.dep.coord.x, self.arr.coord.y - self.dep.coord.y)
        if windPlan:
            self.windvect = windPlan.windGlobal(self.dep.coord, self.arr.coord)
            if abs(self.windvect) != 0:
                self.windangle = ab_vect.angle(self.windvect)
                vent_effectif = abs(self.windvect) * cos(self.windangle)
                self.deviation = (60 / airplane.v_c) * abs(self.windvect) * sin(self.windangle) * (pi / 180)
                self.groundspeed = vent_effectif + airplane.v_c * cos(self.deviation)
                self.duration = abs(ab_vect) / self.groundspeed
            else:
                self.windangle = 0
                self.deviation = 0
                self.groundspeed = airplane.v_c
                self.duration = abs(ab_vect) / self.groundspeed
        else:
            self.windangle = 0
            self.deviation = 0
            self.groundspeed = airplane.v_c
            self.duration = abs(ab_vect) / self.groundspeed


def arbre_creation(filename):
    """arbre_creation(str) return Graph
    renvoie le graphe formé par l'ensemble des aerodromes"""
    aerodrome_coords = geometry.from_file(filename)
    graphe = Graph()
    for (id_oaci, coord) in aerodrome_coords.items():
        node = Node(id_oaci, coord)
        graphe.add(node)
    return graphe


def diagonal(node1, node2, airplane, windPlan):
    """
    :param node1: Node premier aerodrome
    :param node2: Node deuxième aerodrome
    :param airplane: tavel.Airplane avion considéré
    :param windPlan: wind.WindPlan
    :param with_wind: bool avec ou sans vent
    :return: float durée en seconde
    renvoie l'estimation de la durée du trajet direct entre node1 et node2"""
    if node1.id == node2.id:
        return 0
    else:
        edge = Edge(node1, node2)
        edge.calcul(airplane, windPlan=windPlan)
        return edge.duration


def hms(s):
    """hms(int) return str
    convertion d'une durée en seconde au format hh:mm:ss"""
    return "{:02d}:{:02d}:{:02d}".format(int(s) // 3600, int(s) // 60 % 60, int(s) % 60)


def time(str_hms):
    """time(str) return int
    conversion d'une durée au format hh:mm:ss en une durée en seconde"""
    l = str_hms.replace(':', ' ').split()
    return (int(l[0]) * 3600 + int(l[1]) * 60 + int(l[2]))


def get_wind3D(wind3D_dict, sec):
    """get_win3D(dict, float) return wind.Wind3D
    renvoie les vents dont la date est la plus proche de sec"""
    t = int(hms(sec).replace(':', ''))
    (date, wind3D) = min(wind3D_dict.items(), key=lambda x: abs((x[0] % 1e6) - t))
    return wind3D


def astar(flight, airplane, graphe, wind3D_dict):
    """astar(travel.Flight, travel.Airplane, Graph, dict) return Flight
    return flight en actualisant flight.duration et flight.path"""
    openset = set()
    closedset = set()
    current = flight.dep
    # ajouter le noeud initial à openset
    openset.add(current)
    # tant que openset n'est pas vide
    while openset:
        # trouver dans openset le noeud avec le plus petit G + H
        current = min(openset, key=lambda node: node.G + node.H)
        current_id = current.id

        # si le noeud correspond à l'arriver
        if current_id == flight.arr.id:
            duration = current.G  # la durrée du trajet
            path = []  # initialisation du chemin
            # remplir path
            while current_id:
                path.append(current_id)
                current_id = graphe.nodes_dict[current_id].parent
            flight.duration = duration
            flight.path = path[-1::-1]
            for i in range(1, len(flight.path)):
                id = flight.path[i]
                edge = graphe.parent_edge[id]
                flight.edges.append(edge)
            return flight

        # supprimer le noeud de openset
        openset.remove(current)
        # ajouter le noeud à closed set
        closedset.add(current)

        if wind3D_dict:
            wind3D = get_wind3D(wind3D_dict, flight.time_start + current.G)
            windPlan = wind3D.dict[flight.pression]
        if not wind3D_dict:
            windPlan = None

        # parcourir les noeuds voisins
        for (id, edge) in current.voisins(airplane, graphe, windPlan).items():
            node = graphe.nodes_dict[id]
            # si node est déjà dans closedset
            if node in closedset:
                # vérifier s'il vaut mieux passer pr current
                new_g = current.G + edge.duration
                if node.G > new_g:
                    # si c'est le cas, actualiser le parent de node à current
                    node.G = new_g
                    node.parent = current_id
                    graphe.parent_edge[id] = edge
                    # remettre node dans openset
                    openset.add(node)
                    # supprimer node de closedset
                    closedset.remove(node)
            # sinon, si node est déjà dans openset
            elif node in openset:
                # vérifier s'il vaut mieux passer pr current
                new_g = current.G + edge.duration
                if node.G > new_g:
                    # si c'est le cas, actualiser le parent de node à current
                    node.G = new_g
                    node.parent = current_id
                    graphe.parent_edge[id] = edge
            else:
                # sinon, calculer G et H de node
                node.G = current.G + edge.duration
                node.H = diagonal(node, flight.arr, airplane, windPlan)
                # actualiser le parent de node à current
                node.parent = current_id
                graphe.parent_edge[id] = edge
                # ajouter node à openset
                openset.add(node)
    # si l'arriver n'est pas atteint lever l'erreur "NoPathError"
    raise NoPathError


class NoPathError(Exception): pass


def find_path(dep, arr, timeStart, airplane, graphe, wind3D_dict=None):
    """
    :param dep: Node aérodrome de départ
    :param arr: Node aérodrome d'arrivé
    :param timeStart: str heure de départ au format hh:mm:ss
    :param airplane: travel.Airplane aéronef utilisé
    :param graphe: Graph graphe des aérodromes
    :param wind3D_dict: dict dictionnaire de tous les vents de la journé courante
    :return: travel.Flight
    renvoie le chemin optimal
    """
    if wind3D_dict:
        dico = {}
        wind3D = list(wind3D_dict.values())[0]
        for pression in wind3D.dict:
            if airplane.pression_inf <= pression <= airplane.pression_sup:
                flight = travel.Flight(dep, arr, pression, time(timeStart))
                dico[pression] = astar(flight, airplane, graphe, wind3D_dict)
        return min(dico.values(), key=lambda x: x.duration)
    flight = travel.Flight(dep, arr, airplane.pression_inf, time(timeStart))
    return astar(flight, airplane, graphe, wind3D_dict)
