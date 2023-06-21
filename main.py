import random
from random import randrange as rr, randbytes
from tkinter import Tk, BOTH, Canvas
from collections import namedtuple
from typing import Self
from time import sleep
from sys import setrecursionlimit

setrecursionlimit(2**13)


class Point:
    def __init__(self, x, y):
        self.y = y
        self.x = x

    def __lt__(self, other):
        return self.x + self.y < other.x + other.y

    def __le__(self, other):
        return self.x + self.y <= other.x + other.y

    def __eq__(self, other):
        return self.x + self.y == other.x + other.y

    def __ne__(self, other):
        return self.x + self.y != other.x + other.y

    def __gt__(self, other):
        return self.x + self.y > other.x + other.y

    def __ge__(self, other):
        return self.x + self.y >= other.x + other.y

    def __str__(self):
        return f"{self.x}. {self.y}"

    def point_between(self, point_2: Self):
        x1, y1, = (self.x+point_2.x)//2, (self.y+point_2.y)//2
        return Point(x1, y1)


class Line:
    def __init__(self, p1: Point, p2: Point, color="black", width=4):
        self.p1 = min(p1, p2)
        self.p2 = max(p1, p2)
        self.color = color
        self.width = width

    def __repr__(self):
        return f"p1:{self.p1}, p2:{self.p2}"

    def draw(self, canvas: Canvas, fill_color=None, width=None, path_way_offset=None):
        if fill_color is None:
            fill_color = self.color
        if width is None:
            width = self.width
        x1, y1, x2, y2 = self.p1.x, self.p1.y, self.p2.x, self.p2.y
        if path_way_offset:
            if path_way_offset is True:
                path_way_offset = width//2
            x1, x2 = (x1+path_way_offset, x2-path_way_offset) if x1 != x2 else (x1, x2)
            y1, y2 = (y1+path_way_offset, y2-path_way_offset) if y1 != y2 else (y1, y2)

        canvas.create_line(
            x1, y1, x2, y2, fill=fill_color, width=width
        )
        canvas.pack()


class Cell:
    def __init__(self, p1: Point, p2: Point, line_width=4):
        self.has_left_wall = True
        self.has_top_wall = True
        self.has_right_wall = True
        self.has_bottom_wall = True
        self.visited = False
        self._win = False
        top_left_point = tlp = Point(min(p1.x, p2.x), min(p1.y, p2.y))
        bottom_right_point = brp = Point(max(p1.x, p2.x), max(p1.y, p2.y))
        top_right_point = trp = Point(brp.x, tlp.y)
        bottom_left_point = blp = Point(tlp.x, brp.y)
        self.center = tlp.point_between(brp)
        exist_side = namedtuple("exist_side", 'exist line')
        self.cell_sides = {
            "left": exist_side(lambda: self.has_left_wall, Line(tlp, blp)),
            "top": exist_side(lambda: self.has_top_wall, Line(tlp, trp)),
            "right": exist_side(lambda: self.has_right_wall, Line(brp, trp)),
            "bottom": exist_side(lambda: self.has_bottom_wall, Line(brp, blp))
        }
        self.line_width = line_width

    def reverse_exist(self):
        self.has_left_wall = not self.has_left_wall
        self.has_top_wall = not self.has_top_wall
        self.has_right_wall = not self.has_right_wall
        self.has_bottom_wall = not self.has_bottom_wall

    def draw(self, canvas: Canvas, fill_color="black", path_way_offset=None, line_width=None):
        if line_width is None:
            line_width = self.line_width

        for side in self.cell_sides.values():
            if side.exist():
                side.line.draw(canvas, fill_color, path_way_offset=path_way_offset, width=line_width)

    def cell_to_cell_line(self, to_cell: Self, color=None, undo=False):
        if color is None:
            color = "red"
        color = (color, "gray")[undo]
        line_between_cells = Line(self.center, to_cell.center, color=color)
        return line_between_cells

    def draw_move(self, to_cell: Self, canvas: Canvas, undo=False):
        self.cell_to_cell_line(to_cell, undo=undo).draw(canvas)

    def is_win(self):
        return self._win


class Maze:
    def __init__(self, width: int, height: int, num_rows=None, num_cols=None, x1=0, y1=0, win=None, seed=None):
        if num_rows is None or num_cols is None:
            num_cols = height // 27 * 2
            num_rows = num_cols // 2

        self.width = width - x1*2
        self.height = height - y1*2
        self.cell_width = self.width/num_cols
        self.cell_height = self.height/num_rows
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.x = x1
        self.y = y1
        self.start_point = Point(x1, y1)
        self.end_point = Point(x1+self.cell_width*num_cols, y1+self.cell_height*num_rows)
        if seed is not None:
            random.seed(seed)
        if win is None:
            win = rr(1, num_rows*num_cols+1)
        matrix_coordinate = namedtuple("matrix_coordinate", "row column")
        self.win = matrix_coordinate(win//num_rows, win % num_cols)
        self._create_cells()

    def _create_cells(self):
        self._cells = []
        for y in range(self.num_rows):
            row = list()
            for x in range(self.num_cols):
                p1 = Point(self.cell_width*x + self.x, self.cell_height*y + self.y)
                p2 = Point(self.cell_width*(x+1) + self.x, self.cell_height*(y+1) + self.y)
                cell = Cell(p1, p2)
                row.append(cell)
            self._cells.append(row)

    def _break_entrance_and_exit(self):
        self._path_way_cells = list()
        self._solve_lines = list()
        entrance_cell = self._cells[0][0]
        exit_cell = self._cells[-1][-1]

        entrance_cell.has_left_wall = False

        exit_cell.has_right_wall = False
        exit_cell._win = True

    def _break_walls_r(self, i=0, j=0):
        cell = self._cells[i][j]
        if cell.visited:
            return
        self._path_way_cells.append(cell)
        cell.visited = True
        cell.reverse_exist()
        ways = random.sample(["left", "top", "right", "bottom"], 4)
        while ways:
            way = ways.pop()
            if way == "left":
                if j > 0 and not self._cells[i][j - 1].visited:
                    cell.has_left_wall = True
                    self._break_walls_r(i, j-1)
            if way == "top":
                if i > 0 and not self._cells[i - 1][j].visited:
                    cell.has_top_wall = True
                    self._break_walls_r(i-1, j)
            if way == "right":
                if j < self.num_cols - 1 and not self._cells[i][j+1].visited:
                    cell.has_right_wall = True
                    self._break_walls_r(i, j+1)
            if way == "bottom":
                if i < self.num_rows - 1 and not self._cells[i+1][j].visited:
                    cell.has_bottom_wall = True
                    self._break_walls_r(i+1, j)

    def _solve_r(self, i=0, j=0, line_color=None, previous_cell=None):
        cell = self._cells[i][j]
        if cell.visited:
            return False
        if previous_cell:
            self._solve_lines.append(cell.cell_to_cell_line(previous_cell, color=line_color, undo=False))
        cell.visited = True
        ways = random.sample(["left", "top", "right", "bottom"], 4)
        while ways and not self._cells[-1][-1].visited:
            way = ways.pop()
            is_success = False
            if way == "left":
                if cell.has_left_wall and j > 0 and not self._cells[i][j - 1].visited:
                    is_success = self._solve_r(i, j-1, previous_cell=cell, line_color=line_color)
            elif way == "top":
                if cell.has_top_wall and i > 0 and not self._cells[i - 1][j].visited:
                    is_success = self._solve_r(i-1, j, previous_cell=cell, line_color=line_color)
            elif way == "right":
                if cell.has_right_wall and j < self.num_cols - 1 and not self._cells[i][j+1].visited:
                    is_success = self._solve_r(i, j+1, previous_cell=cell, line_color=line_color)
            elif way == "bottom":
                if cell.has_bottom_wall and i < self.num_rows - 1 and not self._cells[i+1][j].visited:
                    is_success = self._solve_r(i+1, j, previous_cell=cell, line_color=line_color)
            if is_success:
                break
        if self._cells[-1][-1].visited:
            return True
        else:
            if previous_cell:
                self._solve_lines.append(cell.cell_to_cell_line(previous_cell, undo=True))

    def _reset_cells_visited(self):
        for cell in self._path_way_cells:
            cell.visited = False

    def maze_matrix(self):
        return self._cells

    def solve_lines(self, line_color=None):
        self._solve_r(line_color=line_color)
        return self._solve_lines

    def path_way_cells(self):
        self._break_entrance_and_exit()
        self._break_walls_r()
        self._reset_cells_visited()
        return self._path_way_cells


class Window:
    def __init__(self):
        self.__root = Tk()
        self.__root.title = 'maze_screen_saver'
        self.canvas = Canvas(self.__root, background="white")
        self.canvas.pack(fill='both', expand=True)
        self.running = True
        self.__root.attributes('-fullscreen', True)
        self.__root.withdraw()
        self.__root.deiconify()
        self.__root.bind("<F11>", lambda event: self.fullscreen_toggle())
        self.__root.bind("<Escape>", lambda event: self.close())
        self.__root.protocol("WM_DELETE_WINDOW", self.close)
        width = self.__root.winfo_screenwidth()
        height = self.__root.winfo_screenheight()
        resolution_tuple = namedtuple('resolution', 'width height')
        self.resolution = resolution_tuple(width, height)

    def redraw(self):
        self.__root.update_idletasks()
        self.__root.update()

    def wait_for_close(self):
        self.running = True
        while self.running:
            self.redraw()

    def clear(self):
        self.canvas.delete("all")

    def close(self):
        self.running = False

    def fullscreen_toggle(self):
        self.__root.attributes("-fullscreen", not self.__root.attributes("-fullscreen"))

    def draw_line(self, line: Line, fill_color="black"):
        line.draw(self.canvas, fill_color)

    def draw_cell(self, cell: Cell, fill_color="black"):
        cell.draw(self.canvas, fill_color)

    def draw_line_connected_two_cell(self, cell_1: Cell, cell_2: Cell):
        cell_1.draw_move(cell_2, self.canvas)

    def draw_maze(self, maze: Maze, animated=True, line_width=4):
        Cell(maze.start_point, maze.end_point).draw(self.canvas, path_way_offset=-2)
        maze_matrix = maze.maze_matrix()
        for row in maze_matrix:
            for cell in row:
                cell.draw(self.canvas)
                if animated:
                    self.redraw()
                    sleep(0.0001)
                if not self.running:
                    break
            if not self.running:
                break
        path_way_cells = maze.path_way_cells()
        for cell in path_way_cells:
            cell.draw(self.canvas, fill_color="white", path_way_offset=True)
            if animated:
                self.redraw()
                sleep(0.0001)
            if not self.running:
                break

    def solve_maze(self, maze: Maze, animated=True, random_line_color=False):
        line_color = [None, f"#{randbytes(3).hex()}"][random_line_color]
        solve_lines = maze.solve_lines(line_color=line_color)
        for line in solve_lines:
            line.draw(self.canvas)
            if animated:
                self.redraw()
                sleep(0.05)
            if not self.running:
                break


if __name__ == '__main__':
    win = Window()
    while win.running:
        main_maze = Maze(win.resolution.width, win.resolution.height, x1=56, y1=42)
        win.draw_maze(main_maze)
        win.solve_maze(main_maze, random_line_color=True)
        win.clear()
