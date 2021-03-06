from copy import copy, deepcopy
from helper_funcs import *


class Vertex:
    def __init__(self, index, fld_chance, graph=None, v_type='P', ppl_count=0):
        """
        :type ppl_count: int
        :type v_type: str
        :type fld_chance: float
        :type index: int
        """
        self.index = index
        self.pv = fld_chance
        self.is_flooded = False

        self.connected_edges = []  # type: list[Edge]

        # is 'S' if it's a shelter, is 'P' if people location:
        self.v_type = v_type
        self.ppl_count = ppl_count
        self.graph = graph

    def add_edge(self, edge):
        self.connected_edges.append(edge)

    def is_shelter(self):
        return self.v_type == 'S'

    def is_ppl_location(self):
        return self.v_type == 'P'

    def get_connected_vertices(self):
        res = []
        for e in self.connected_edges:
            if e.vertex_1 == self:
                res.append(e.vertex_2)
            else:
                res.append(e.vertex_1)
        return res

    def get_connected_vertices_with_weights(self):
        res = []
        for e in self.connected_edges:
            if e.vertex_1 == self:
                res.append((e.vertex_2, e.weight))
            else:
                res.append((e.vertex_1, e.weight))
        return res

    def __str__(self):
        return "V" + str(self.index)

    def __eq__(self, other):
        if isinstance(other, Vertex):
            return self.index == other.index
        else:
            return False


class Edge:
    def __init__(self, index, vertex_1, vertex_2, weight):
        """
        :type index: int
        :type vertex_1: Vertex
        :type vertex_2: Vertex
        :type weight: int
        """
        self.index = index
        self.vertex_1 = vertex_1
        self.vertex_2 = vertex_2
        self.weight = weight
        self.is_blocked = False

    def block_road(self):
        self.is_blocked = True

    def __str__(self):
        return "E" + str(self.index)

    def __eq__(self, other):
        if isinstance(other, Edge):
            return self.index == other.index
        else:
            return False


class Graph:

    P_LEAKAGE = 0.001

    def __init__(self, file_path):
        self.vertices = []  # type: list[Vertex]
        self.edges = []  # type: list[Edge]
        self.number_of_vertices = 0
        self.p_persistence = 0.0
        self.p_leakage = Graph.P_LEAKAGE

        # Reading configuration file
        n = None
        f = open(file_path, "r")
        print_debug("---------------------Building Graph---------------------")
        for line in f:
            if line[0] == '#':
                line_info = line.split('  ')[0][1:]
                line_info_split = line_info.split(' ')
                if line_info[0] == 'N':  # N x
                    n = int(line_info_split[1])
                    print_debug("Got N=" + str(n))
                elif line_info[0] == 'V' and line_info_split[1] == 'F':  # Vx F pv
                    vertex_index = int(line_info_split[0][1:])  # Vx
                    vertex_fld_chance = float(line_info_split[2])  # pv
                    self.vertices.append(Vertex(vertex_index, vertex_fld_chance, self))
                    print_debug("Got V" + str(vertex_index) + ": fld_chance=" + str(vertex_fld_chance))
                elif line_info_split[0] == 'Ppersistence':  # Ppersistence ppersistence
                    # We're done with vertices, so put this check here:
                    inp_v_len = len(self.vertices)
                    if n != inp_v_len:
                        print_info("N is different from number of actual vertices. adding probability 0 to them!")
                        for i in range(n)[inp_v_len:]:
                            self.vertices.append(Vertex(i+1, 0.0, self))
                    # Back to persistence :)
                    self.p_persistence = float(line_info_split[1])
                    print_debug("Got Ppersistence=" + str(self.p_persistence))
                elif line_info[0] == 'E':  # Ex x x Wx
                    edge_index = int(line_info_split[0][1:])  # Ex
                    edge_v1_index = int(line_info_split[1])  # x
                    edge_v2_index = int(line_info_split[2])  # x
                    edge_weight = int(line_info_split[3][1:])  # Wx
                    e = Edge(edge_index, self.vertices[edge_v1_index-1], self.vertices[edge_v2_index-1], edge_weight)
                    self.edges.append(e)
                    self.vertices[edge_v1_index-1].add_edge(e)
                    self.vertices[edge_v2_index-1].add_edge(e)
                    print_debug("Got E" + str(edge_index))

        f.close()


        print_debug("---------------------Done---------------------")

    def num_of_roads(self):
        return len(self.edges)

    def num_of_vertices(self):
        return len(self.vertices)

    def get_edge(self, v1, v2):
        for e in self.edges:
            if e.vertex_1 == v1 and e.vertex_2 == v2:
                return e
            elif e.vertex_2 == v1 and e.vertex_1 == v2:
                return e
        raise Exception("No edge between " + str(v1) + " and " + str(v2) + ".")

    def get_edge_from_string(self, str_e):
        e_index = int(str_e[1:])
        return self.edges[e_index-1]

    def get_vertex_from_string(self, str_v):
        v_index = int(str_v[1:])
        return self.vertices[v_index-1]

    def get_vertex(self, index):
        return self.vertices[index-1]

    def remove_blocked_edges(self):
        res_g = deepcopy(self)
        tmp_edges = copy(res_g.edges)
        for e in tmp_edges:
            if e.is_blocked:
                e.vertex_1.connected_edges.remove(e)
                e.vertex_2.connected_edges.remove(e)
                res_g.edges.remove(e)

    def get_ppl2save(self):
        res = 0
        for v in self.vertices:
            if not v.is_shelter():
                res += v.ppl_count
        return res

    def get_all_paths(self, source_vertex, dest_vertex, curr_path=[]):
        """
        :type dest_vertex: Vertex
        :type source_vertex: Vertex
        """
        path = curr_path + [source_vertex]
        if source_vertex == dest_vertex:
            return [path]
        paths = []
        for v in self.vertices:
            if v not in path:
                further_paths = self.get_all_paths(v, dest_vertex, path)
                for further_path in further_paths:
                    paths.append(further_path)
        return paths

    def get_paths(self, source_vertex, dest_vertex, curr_path, path_list):
        if source_vertex.__eq__(dest_vertex):
            #curr_path.append(dest_vertex)
            path_list.append(curr_path)
            return path_list

        for v in self.get_connected_vertex(source_vertex):
            if v not in curr_path:
                pathCopy = deepcopy(curr_path)
                pathCopy.append(v)
                self.get_paths(v, dest_vertex, pathCopy, path_list)
        return path_list

    def convert_vertexes_to_edges(self, path):
        src = path[0]
        edges_path = []
        i=0
        for v in path:
            try:
                edges_path.append(self.get_edge(src, path[i+1]))
            except:
                return edges_path
            src = path[i+1]
            i += 1
        return edges_path

    def get_connected_vertex(self, v):
        verticesList = []
        for e in self.edges:
            if e.vertex_1.__eq__(v):
                verticesList.append(e.vertex_2)
            if e.vertex_2.__eq__(v):
                verticesList.append(e.vertex_1)
        return verticesList

    def __str__(self):
        s = str(self.vertices[0]) + "(P " + str(self.vertices[0].pv) + ", "
        if self.vertices[0].is_shelter():
            s = s + str(self.vertices[0].v_type)
        else:
            s = s + "P" + str(self.vertices[0].ppl_count)
        s = s + ")"
        for v in self.vertices[1:]:
            s = s + ", " + str(v) + "(P " + str(v.pv) + ", "
            if v.is_shelter():
                s = s + str(v.v_type)
            else:
                s = s + "P" + str(v.ppl_count)
            s = s + ")"
        s = s + "\n"
        s = s + str(self.edges[0]) + ": " + str(self.edges[0].vertex_1) + " -" + str(self.edges[0].weight) + "- " + \
            str(self.edges[0].vertex_2)
        for e in self.edges[1:]:
            s = s + "\n" + str(e) + ": " + str(e.vertex_1) + " -" + str(e.weight) + "- " + str(e.vertex_2)
        return s
