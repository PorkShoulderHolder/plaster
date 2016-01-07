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

class PlasterError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Plaster(object):
    def __init__(self, d = 50, t = 300, cd = 12):
        self.sig_places = []
        self.traces = []
        self.times = []
        self.d_thresh = d # in meters
        self.t_thresh = t # in seconds
        self.cd_thresh = cd # in meters
        self.current_start = None
        self.centroids = []
        self.current_cluster = None
        self.pending_location = None
        self.d_metric = lambda ll,cluster: equirectangular_approx(ll, avg_loc(cluster))

    def start_temp_cluster(self,trace,t):
        self.current_cluster.append(trace)
        self.pending_location = None
        self.current_start = t

    def subsume_cluster(self, cluster):
        """
        Add a set of new locations (current cluster) to the list of significant places, while checking for overlap
        with existing places
        """
        min_ind = len(self.sig_places)
        min_d = 999999999999999
        for i,place in enumerate(self.sig_places):
            cd = equirectangular_approx(avg_loc(cluster),avg_loc(place))
            if cd < min_d:
                min_d, min_ind = cd, i
        if min_d < self.cd_thresh:
            self.sig_places[min_ind].extend(cluster)
            self.centroids[min_ind] = avg_loc(self.sig_places[min_ind])
        else:
            self.sig_places.append(cluster)
            self.centroids[min_ind] = avg_loc(cluster)
        return min_ind

    def cluster_point(self, trace, t):
        """
        Add new lat, lng, pair to clustering model.
        Points must be added in chronological order
        """
        if t < self.times[-1]:
            raise PlasterError("Data point {0}, at {1} not in Chronological Order".format(trace, t))
        self.times.append(t)
        self.traces.append(trace)

        if self.current_cluster is None or self.d_metric(trace,self.current_cluster) < self.d_thresh:
            self.start_temp_cluster(trace,t)
        elif self.pending_location is not None:
            if t - self.current_start > self.t_thresh:
                self.subsume_cluster(self.current_cluster)
            self.current_cluster = [self.pending_location]
            if self.d_metric(trace,self.current_cluster) < self.d_thresh:
                self.start_temp_cluster(trace,t)
            else:
                self.pending_location = trace
        else:
            self.pending_location = trace

    def fit(self, traces, ts):
        """
        methods to conform to scikit learn format, batch learning
        """
        for trace, t in zip(traces,ts):
            self.cluster_point(trace,t)

    def predict(self,traces,ts):
        """
        we use all data, this is an unsupervised technique
        """
        self.fit(traces,ts)
