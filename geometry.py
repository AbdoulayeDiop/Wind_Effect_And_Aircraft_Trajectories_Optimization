from numpy import arccos, cos, pi


class Point(object):
    def __init__(self, a, b, lat_moy=None):
        self.lat_moy = lat_moy
        if lat_moy != None:
            self.long = a
            self.lat = b
            rayon_terrestre = 6371000
            long_to_x = rayon_terrestre * cos(lat_moy * pi / 180) * (pi / 180)
            lat_to_y = rayon_terrestre * (pi / 180)
            self.x = self.long * long_to_x
            self.y = self.lat * lat_to_y
        else:
            self.x = a
            self.y = b

    def __repr__(self):
        return "({0.long}, {0.lat})".format(self) if self.lat_moy != None else "({0.x}, {0.y})".format(self)

    def __eq__(self, other):
        if self.lat_moy != None:
            return self.long == other.long and self.lat == other.lat
        else:
            return self.x == other.x and self.y == other.y

    def __sub__(self, other):
        if self.lat_moy != None:
            return Point(self.long - other.long, self.lat - other.lat, self.lat_moy)
        else:
            return Point(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        if self.lat_moy != None:
            return Point(self.long + other.long, self.lat + other.lat, self.lat_moy)
        else:
            return Point(self.x + other.x, self.y + other.y)

    def __rmul__(self, k):
        if self.lat_moy != None:
            return Point(k * self.long, k * self.lat, self.lat_moy)
        else:
            return Point(k * self.x, k * self.y)

    def __abs__(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def distance(self, other):
        return abs(self - other)

    def adapt_scale(self, view_width, liste):
        """ adapt scale(int, list) return geometry.Point
        renvoie les coordonnées pixélisées de self"""
        min_x, max_x, min_y, max_y = liste
        width = max_x - min_x
        height = max_y - min_y
        view_height = view_width * height / width
        pt = Point(self.long, self.lat, self.lat_moy)
        pt.x = (pt.x - min_x) * view_width / width
        pt.y = (max_y - pt.y) * view_height / height
        return pt


class Vect():
    def __init__(self, u, v):
        self.u = u
        self.v = v

    def __repr__(self):
        return "({0.u}, {0.v})".format(self)

    def __eq__(self, other):
        return self.u == other.u and self.v == other.v

    def __sub__(self, other):
        return Vect(self.u - other.u, self.v - other.v)

    def __add__(self, other):
        return Vect(self.u + other.u, self.v + other.v)

    def __rmul__(self, k):
        return Vect(k * self.u, k * self.v)

    def __abs__(self):
        return (self.u ** 2 + self.v ** 2) ** 0.5

    def sca(self, other):
        """sca(Point) return float
        returns the scalar product between self and other"""
        return self.u * other.u + self.v * other.v

    def det(self, other):
        """det(Vect) return float
        returns the determinant between self and other"""
        return self.u * other.v - self.v * other.u

    def angle(self, other):
        return arccos(self.sca(other) / (abs(self) * abs(other)))


def find_latmoy(file):
    """find_latmoy(str) return float
    renvoie la latitude moyenne de l'ensemble des aérodromes considèrés"""
    with open(file, "r") as f:
        liste = []
        for line in f:
            l = line.strip().split()
            liste.append(float(l[-1]))
    return (min(liste) + max(liste)) / 2


def from_file(file):
    """from_file(str) return dict
    renvoie le dictionnaire de l'ensemble des aérodromes considèrés"""
    dict = {}
    m = find_latmoy(file)
    with open(file, "r") as f:
        for line in f:
            l = line.strip().split()
            long, lat = float(l[-2]), float(l[-1])
            dict[l[1]] = Point(long, lat, lat_moy=m)
    return dict
