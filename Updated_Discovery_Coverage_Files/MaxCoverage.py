import math
import csv


class Node:
    def __init__(self, x, y, amount_covered, long, lad):
        self.x = x
        self.y = y
        self.long = long
        self.lad = lad
        self.amount_covered = amount_covered


def place_Node(node, cell_coverage_rad, cells_length, cells_width, grid):
    coverage_circ = cell_coverage_rad * 2 + 1
    base_length = node.y - cell_coverage_rad
    base_width = node.x - cell_coverage_rad
    for i in range(coverage_circ):
        for j in range(coverage_circ):
            row = base_length + i
            col = base_width + j
            if 0 <= row < cells_width and 0 <= col < cells_length:
                grid[row][col] = 1  # Covered spot
                node.amount_covered += 1
    return grid


def check_placements(Nodes, index, cell_coverage_rad, cells_length, cells_width, grid):
    if index == len(Nodes):
        positions = [(node.x, node.y) for node in Nodes]
        return positions

    best_grid = None
    amnt_covered = 0
    center_x = cells_length / 2
    center_y = cells_width / 2
    vert_spacing = 0
    for row in range(cells_width):
        if vert_spacing > cell_coverage_rad:
            vert_spacing += 1
            continue
        else:
            vert_spacing = 0
            hor_spacing = 0
            for col in range(cells_length):
                if hor_spacing > cell_coverage_rad:
                    hor_spacing += 1
                    continue
                else:
                    hor_spacing = 0
                    Nodes[index].x = col
                    Nodes[index].y = row
                    Nodes[index].amount_covered = 0
                    new_grid = [row.copy() for row in grid]
                    new_grid = place_Node(Nodes[index], cell_coverage_rad, cells_length, cells_width, new_grid)
                    temp_pos = check_placements(Nodes, index + 1, cell_coverage_rad, cells_length, cells_width,
                                                new_grid)
                    if Nodes[index].amount_covered == 0:
                        continue
                    count = 0

                    for i in range(len(new_grid)):
                        for j in range(len(new_grid[0])):
                            if new_grid[i][j] == 1:
                                count += 1

                    if count > amnt_covered:
                        amnt_covered = count
                        best_grid = temp_pos
    return best_grid


def MaxCoverage(num_of_nodes, area_length, area_width, coverage_rad, ref_long, ref_lat, cell_size):
    Nodes = [Node(0, 0, 0, 0, 0) for _ in range(num_of_nodes)]

    cell_coverage_rad = math.ceil(coverage_rad / cell_size)
    print("with Coverage Radius of " + str(coverage_rad) + ", the cell coverage is " + str(cell_coverage_rad))
    cells_length = math.floor(area_length / cell_size)
    print(
        "with area length of " + str(area_length) + ", the amount of cells needed to cover it is " + str(cells_length))
    cells_width = math.floor(area_width / cell_size)
    print("with area length of " + str(area_width) + ", the amount of cells needed to cover it is " + str(cells_width))
    grid = [[0 for _ in range(cells_length)] for _ in range(cells_width)]

    positions = check_placements(Nodes, 0, cell_coverage_rad, cells_length, cells_width, grid)
    print(positions)
    i = 0

    for a in Nodes:
        a.x = positions[i][0]
        a.y = positions[i][1]
        grid = place_Node(a, cell_coverage_rad, cells_length, cells_width, grid)
        i += 1

    lat = ref_lat
    long = ref_long
    count = 0
    data = [[] for _ in range(num_of_nodes)]
    for node in Nodes:
        grid[node.y][node.x] = 2
        node.lat = round(lat + (cell_size * node.y) / 111.32, 6)
        node.long = round(long + (cell_size * node.x) / (111.32 * math.cos(lat * (math.pi / 180))), 6)
        data[count].append(node.long)
        data[count].append(node.lat)
        data[count].append(1.5)
        count += 1
        print("Node", count, "long: ", node.long)
        print("Node", count, "lat : ", node.lat)
    print("\nGRID (2 - NODE LOCATION, 1 - COVERED CELL, 2 - UNCOVERED CELL)")
    for row in grid:
        print(row)
    return data


if __name__ == "__main__":
    num_of_nodes = 2
    area_length = 50
    area_width = 60
    coverage_radius = 10
    ref_long = 134.7625
    ref_lat = -12.4872

    print(
        f"\nNodes: {num_of_nodes}, Area Length: {area_length}, Area Width: {area_width}, Coverage Radius: {coverage_radius}, Reference Long: {ref_long}, Reference Lat: {ref_lat}\n")
    MaxCoverage(2, 50, 60, 10, 134.7625, -12.4872)
