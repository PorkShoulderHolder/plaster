__author__ = 'sam.royston'
import numpy as np
import math

def equirectangular_approx(ll1, ll2):
    """
    faster than haversine, ok for short distances
    """
    earth_radius = 6371 # in km
    x = (ll2 - ll1) * math.cos( 0.5*(ll1 + ll2))
    y = ll2 - ll1
    return earth_radius * math.sqrt((x*x) + (y*y))

def avg_loc(cluster):
    c = np.array(cluster)
    return np.average(c)

def time_in_cluster(cluster):

class Plaster(object):
    def __init__(self, d = 50, t = 300, cd = 12):
        self.sig_places = []
        self.traces = []
        self.times = []
        self.d_thresh = d # in meters
        self.t_thresh = t # in seconds
        self.cd_thresh = cd # in meters
        self.current_start = None
        self.current_cluster = None
        self.pending_location = None
        self.d_metric = lambda ll,cluster: equirectangular_approx(ll, avg_loc(cluster))


    def cluster_point(self, trace, t):
        """
        Add new lat, lng, pair to clustering model.
        Points must be added in chronological order
        """
        self.times.append(t)
        self.traces.append(trace)
        if self.current_cluster is None or self.d_metric(trace,self.current_cluster) < self.d_thresh:
            self.current_cluster.append(t)
            self.pending_location = None
            self.current_start = t
        elif self.pending_location is not None:
            if t - self.current_start > self.t_thresh:
                self.subsume_cluster(self.current_cluster)


    def subsume_cluster(self, cluster):
        """
        Add a set of new locations (current cluster) to the list of significant places, while checking for overlap
        with existing places
        """
        min_ind = 0
        min_d = 999999999999
        for i,place in enumerate(self.sig_places):
            cd = equirectangular_approx(avg_loc(cluster),avg_loc(place))
            if cd < min_d:
                min_d, min_ind = cd, i
        if min_d < self.cd_thresh:
            self.sig_places.extend(cluster)

