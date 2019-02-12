import geometry
import numpy as np


class Wind3D:
    """Description du vent global à une date donnée (ensemble des vents locaux sur l'ensemble des altitudes),
    avec les attributs suivants:
            - date: int (date des mesures)
            - dict: dict[key= altitude] = windPlan"""

    def __init__(self, date):
        self.date = date
        self.dict = {}

    def __repr__(self):
        return "<wind.Wind3D {0.date}>".format(self)

    def add_windPlan(self, windPlan):
        self.dict[windPlan.alt] = windPlan

    def get_windPlan(self, alt):
        return self.dict[alt]


class WindPlan(Wind3D):
    """Description du vent à une altitude donnée (ensemble des vents locaux), avec les attributs suivants:
        - alt: int (altitude des mesures)
        - list: np.array (liste des mesures sur le plan)
        - date: int (date des mesures)"""

    def __init__(self, alt, date):
        super().__init__(date)
        self.alt = alt
        self.dict = {}

    def __repr__(self):
        return "<wind.WindPlan {0.alt}>".format(self)

    def add_windLocal(self, wind):
        self.dict[(wind.coord.long, wind.coord.lat)] = wind

    def get_windLocal(self, coord):
        return self.dict[(coord.long, coord.lat)]

    def windGlobal(self, a, b):
        """
        :param a: geometry.Coord
        :param b: geometry.Coord
        :return: geométry.vect
        renvoie le vecteur vent moyen entre a et b
        """
        n = 0
        if abs(a.long - b.long) >= abs(a.lat - b.lat):
            k1 = int(min(a.long, b.long) / 0.5)
            k2 = int(max(a.long, b.long) / 0.5) + 1
            vent = geometry.Vect(0, 0)
            for i in range(k1, k2 + 1):
                x = i * 0.5
                if b.long - a.long != 0:
                    y = (b.lat - a.lat) / (b.long - a.long) * (x - a.long) + a.lat
                    try:
                        vent += self.dict[(x, int(y / 0.5) * 0.5)].vect
                        n += 1
                    except KeyError:
                        pass
                    try:
                        vent += self.dict[(x, int(y / 0.5 + 1) * 0.5)].vect
                        n += 1
                    except KeyError:
                        pass
        else:
            k1 = int(min(a.lat, b.lat) / 0.5)
            k2 = int(max(a.lat, b.lat) / 0.5) + 1
            vent = geometry.Vect(0, 0)
            for i in range(k1, k2 + 1):
                y = i * 0.5
                if b.lat - a.lat != 0:
                    x = (b.long - a.long) / (b.lat - a.lat) * (y - a.lat) + a.long
                    try:
                        vent += self.dict[(int(x / 0.5) * 0.5), y].vect
                        n += 1
                    except KeyError:
                        pass
                    try:
                        vent += self.dict[(int(x / 0.5 + 1) * 0.5, y)].vect
                        n += 1
                    except KeyError:
                        pass

        return vent.__rmul__(1 / n) if n else min(self.dict.values(), key=lambda x: abs(x.coord - a)).vect


class WindLocal(WindPlan):
    """Description du vent local (mesure point), avec les attributs suivants:
        - u: float (vitesse du vent en m/s suivant l'est)
        - v: float (vitesse du vent en m/s suivant le nord)
        - coord: Point tuple (coordonnées géographiques des mesures)
        - alt: int (altitude de la mesure)
        - date: int (date de la mesure)"""

    def __init__(self, coord, alt, date):
        super().__init__(alt, date)
        self.coord = coord
        self.u = None
        self.v = None
        self.vect = None

    def __repr__(self):
        return "<wind.WindLocal {0.vect} {0.coord}>".format(self)

    def add_valToVect(self, val, param):
        if param == 'u':
            self.u = val
        if param == 'v':
            self.v = val
        self.vect = geometry.Vect(self.u, self.v)

    def get_dir(self):
        return np.arctan2(self.v, self.u)

    def get_speed(self):
        return abs(self.vect)


def from_file(filename, m):
    """from_file(str) return Wind3D : reads a wind map description file"""
    wind3D_dict = {}
    coord = None
    alt = None
    date = None
    param = None

    file = open(filename)
    for line in file:
        words = line.strip().split()
        if 'U' in words:
            param = 'u'
        if 'V' in words:
            param = 'v'
        if words[0] == 'NIVEAU':
            alt = int(words[2])
            date = int(words[6])
            if date not in wind3D_dict:
                wind3D = Wind3D(date)
                wind3D_dict[date] = wind3D
                windPlan = WindPlan(alt, date)
                wind3D.add_windPlan(windPlan)
            else:
                wind3D = wind3D_dict[date]
                if alt not in wind3D.dict:
                    windPlan = WindPlan(alt, date)
                    wind3D.add_windPlan(windPlan)
        if words[0] == 'LONGITUDE':
            long = int(words[1]) / 1000
            lat = int(words[3]) / 1000
            val = float(words[5])
            coord = geometry.Point(long, lat, m)
            wind3D = wind3D_dict[date]
            windPlan = wind3D.get_windPlan(alt)
            if param == 'u':
                windLocal = WindLocal(coord, alt, date)
                windLocal.add_valToVect(val, param)
                windPlan.add_windLocal(windLocal)
            else:
                windPlan.get_windLocal(coord).add_valToVect(val, param)
    file.close()
    return wind3D_dict


def create_wind3D_dict(files, m):
    """create_wind3D_dict(str, float) return dict
    renvoie le dictionnaire des wind3D en tenant compte de m(latitude moyenne pour la projection mercator)"""
    wind3D_dict = {}
    for file in files:
        for (date, wind3D) in from_file(file, m).items():
            wind3D_dict[date] = wind3D
    return wind3D_dict
