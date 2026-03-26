

class Shape:
    def __init__(self, color):
        self.color = color

class Circle(Shape):
    def __init__(self, radius, color):
        super().__init__(color)
        self.radius = radius

        
class Triangle:
    def __init__(self, width, height, color):
        self.color = color
        self.width = width
        self.height = height

class Square:
    def __init__(self, width, color):
        self.color = color
        self.width = width


        