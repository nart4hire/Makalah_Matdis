from numpy import int32, float32, sqrt
from time import time
from PIL import Image
from sys import argv

### Main Functions
def FISR(input: float, accurate: bool = False) -> float:
    """ Converts an input float to the inverse square root using the Fast Inverse Square Root algorithm
    """
    # Approximate inverse square root using raw type casting and magic number 0x5f3759df
    approx_float = float32(input)
    cast_int = approx_float.view(int32)
    cast_int = int32(0x5f3759df) - int32(cast_int >> 1)
    approx_float = cast_int.view(float32)

    # Newtonian Iteration
    half = input * 0.5
    approx_float = approx_float * (1.5 - (half * approx_float * approx_float))
    if accurate:
        approx_float = approx_float * (1.5 - (half * approx_float * approx_float))

    return float(approx_float)

def ISR(input: float, inverse: bool = False) -> float:
    """ Converts an input float to the inverse square root using Integer Square Root Algorithm
    """
    # Approximate square root to 1 x 2^e, e = (E - 127) // 2 + 127, E is the biased exponent
    src_float = float32(input)
    cast_int = src_float.view(int32)
    approx_float = (((((0x7f800000 & cast_int) >> 23) - 127) // 2) + 127) << 23

    # Approximate other integers using integer square root
    for i in range(22, -1, -1):                         # For i in range of digits in mantissa - 1 to 0
        increment = 1 << i                              # Increment is 1 at the position i + 1
        est = (approx_float + increment).view(float32)  # set est = approximation + increment in float form
        if (est * est <= src_float):                    # If the original input is more than est ^ 2:
            approx_float += increment                   #     > add increment to approximation
    
    if inverse:
        return 1 / float(approx_float.view(float32))
    return float(approx_float.view(float32))
### End Main Functions

### Vector Class
class Vector:
    def __init__(self, x: float, y: float, z: float):
        self.abscissa = float(x)
        self.ordinate = float(y)
        self.applicate = float(z)

    def __str__(self) -> str:
        return "(%.2f, %.2f, %.2f)" % (self.abscissa, self.ordinate, self.applicate)

    def copy(self):
        copy = Vector(self.abscissa, self.ordinate, self.applicate)
        return copy

    def normalize(self, default: bool = True):
        sum_of_squares = self.abscissa * self.abscissa + self.ordinate * self.ordinate + self.applicate * self.applicate
        if default:
            norm = FISR(sum_of_squares)
        else:
            norm = ISR(sum_of_squares, True)
        self.abscissa *= norm
        self.ordinate *= norm
        self.applicate *= norm
        return self

    def mul_by_factor(self, x: float):
        copy = self.copy()
        copy.abscissa *= x
        copy.ordinate *= x
        copy.applicate *= x
        return copy

    def add_vector(self, v):
        copy = self.copy()
        copy.abscissa += v.abscissa
        copy.ordinate += v.ordinate
        copy.applicate += v.applicate
        return copy

    def length(self) -> float:
        sum_of_squares = self.abscissa * self.abscissa + self.ordinate * self.ordinate + self.applicate * self.applicate
        return (1 / FISR(sum_of_squares))

    def dot(self, v):
        return self.abscissa * v.abscissa + self.ordinate * v.ordinate + self.applicate * v.applicate
### End Vector Class

### Plane Class
class Paraboloid:
    def __init__(self, size: int = 100, light_direction: Vector = Vector(-1, -1, 3), mx: float = 0.15, my: float = 0.15, dx: float = 7.5, dy: float = 7.5, dz: float = 30, default: bool = True):
        self.shape = size
        self.dir = light_direction.normalize(default)
        self.heights = [[dz - (mx * x - dx) ** 2 - (my * y - dy) ** 2 for y in range(size + 2)] for x in range(size + 2)]
        print("height map initialized...")
        if not default:
            self.norms = [[Vector(self.heights[x - 1][y] - self.heights[x + 1][y], self.heights[x][y - 1] - self.heights[x][y + 1], 2).normalize(default) for y in range(1, size + 1)] for x in range(1, size + 1)]
        else:
            self.norms = [[Vector(self.heights[x - 1][y] - self.heights[x + 1][y], self.heights[x][y - 1] - self.heights[x][y + 1], 2).normalize(default) for y in range(1, size + 1)] for x in range(1, size + 1)]
        print("norm map initialized...\n")

    def shade_map(self, num: str = '', specular: bool = True) -> Image:
        if specular:
            Ka = 0.05
            Kd = 0.6
            Ks = 0.2
        else:
            Ka = 0.05
            Kd = 0.6
            Ks = 0
        
        img = Image.new('RGB', (self.shape, self.shape))
        for i in range(self.shape):
            for j in range(self.shape):
                norm = self.norms[i][j]
                ratio = Ka + Kd * norm.dot(self.dir) + Ks * (norm.dot(self.dir.add_vector(Vector(0, 0, 0.5))))
                if ratio > 1:
                    intensity = 255
                else:
                    intensity = round(255 * ratio)
                img.putpixel((i, j), (intensity, intensity, intensity))
        if num != '':
            img.save('test' + num + '.jpg')
        else:
            return img

if __name__ == "__main__":
    hl = 3
    if len(argv) < 2:
        size = 128
    else:
        size = int(argv[1])

    if len(argv) < 3:
        about = 0
    else:
        about = int(argv[2])
        hl = about * 3

    if len(argv) < 4:
        isr = 'n'
    else:
        isr = str(argv[3])

    if len(argv) < 5:
        gif = 'n'
    else:
        gif = str(argv[4])
    
    if len(argv) == 1:
        start = time()
        p = Paraboloid()
        p.shade_map('basic')
        end = time()
        print ('image saved')
        print ('took', end - start, 'seconds')
        exit(0)
    
    if isr in 'y':
        if gif in 'y':
            start = time()
            images = []
            for i in range(-about, about):
                j = sqrt(about ** 2 - i ** 2)
                p = Paraboloid(size, Vector(i, j, hl), default=False)
                images.append(p.shade_map())
            
            for i in range(about, -about, -1):
                j = -sqrt(about ** 2 - i ** 2)
                p = Paraboloid(size, Vector(i, j, hl), default=False)
                images.append(p.shade_map())
            
            images[0].save('test.gif', save_all=True, append_images=images[1:], duration=60, loop=0)
            end = time()
            print ('gif saved')
            print ('took', end - start, 'seconds')
        else:
            start = time()
            qn = 1
            for i in range(-about, about):
                j = sqrt(about ** 2 - i ** 2)
                print ('image ' + str(qn) + ' initializing...')
                p = Paraboloid(size, Vector(i, j, hl), default=False)
                p.shade_map(str(qn))
                qn += 1
            
            for i in range(about, -about, -1):
                j = -sqrt(about ** 2 - i ** 2)
                p = Paraboloid(size, Vector(i, j, hl), default=False)
                p.shade_map(str(qn))
                qn += 1
            end = time()
            print ('image(s) saved')
            print ('took', end - start, 'seconds')
    else:
        if gif in 'y':
            start = time()
            images = []
            for i in range(-about, about):
                j = sqrt(about ** 2 - i ** 2)
                p = Paraboloid(size, Vector(i, j, hl))
                images.append(p.shade_map())
            
            for i in range(about, -about, -1):
                j = -sqrt(about ** 2 - i ** 2)
                p = Paraboloid(size, Vector(i, j, hl))
                images.append(p.shade_map())
            
            images[0].save('test.gif', save_all=True, append_images=images[1:], duration=60, loop=0)
            end = time()
            print ('gif saved')
            print ('took', end - start, 'seconds')
        else:
            start = time()
            qn = 1
            for i in range(-about, about):
                j = sqrt(about ** 2 - i ** 2)
                print ('image ' + str(qn) + ' initializing...')
                p = Paraboloid(size, Vector(i, j, hl))
                p.shade_map(str(qn))
                qn += 1
            
            for i in range(about, -about, -1):
                j = -sqrt(about ** 2 - i ** 2)
                p = Paraboloid(size, Vector(i, j, hl))
                p.shade_map(str(qn))
                qn += 1
            end = time()
            print ('image(s) saved')
            print ('took', end - start, 'seconds')
            