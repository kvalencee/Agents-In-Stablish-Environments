import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


# %% Acción
class Accion:
    def __init__(self, nombre):
        self.nombre = nombre

    def __str__(self):
        return self.nombre


# %% Estado
class Estado:
    def __init__(self, fila, columna):
        self.fila = fila
        self.columna = columna

    def __str__(self):
        return f"({self.fila}, {self.columna})"

    def __eq__(self, otro):
        return self.fila == otro.fila and self.columna == otro.columna

    def __hash__(self):
        return hash((self.fila, self.columna))


# %% Problema
class Problema:
    def __init__(self, estado_inicial, estados_objetivos, laberinto):
        self.estado_inicial = estado_inicial
        self.estados_objetivos = estados_objetivos
        self.laberinto = laberinto

    def __str__(self):
        msg = "Estado Inicial: {0} -> Objetivos: {1}"
        return msg.format(self.estado_inicial, [str(objetivo) for objetivo in self.estados_objetivos])

    def es_objetivo(self, estado):
        return estado in self.estados_objetivos

    def resultado(self, estado, accion):
        fila, columna = estado.fila, estado.columna
        if accion.nombre == "arriba":
            nueva_fila, nueva_columna = fila - 1, columna
        elif accion.nombre == "abajo":
            nueva_fila, nueva_columna = fila + 1, columna
        elif accion.nombre == "izquierda":
            nueva_fila, nueva_columna = fila, columna - 1
        elif accion.nombre == "derecha":
            nueva_fila, nueva_columna = fila, columna + 1
        else:
            return None

        # Verificar si la nueva posición es válida (no es una pared o montaña)
        if (
            0 <= nueva_fila < len(self.laberinto)
            and 0 <= nueva_columna < len(self.laberinto[0])
            and self.laberinto[nueva_fila][nueva_columna] != 0  # Pared
            and self.laberinto[nueva_fila][nueva_columna] != 5   # Montaña
        ):
            return Estado(nueva_fila, nueva_columna)
        return None


# %% Nodo
class Nodo:
    def __init__(self, estado, accion, acciones, padre=None):
        self.estado = estado
        self.accion = accion
        self.acciones = acciones
        self.padre = padre
        self.hijos = []

    def expandir(self, problema):
        for accion in self.acciones:
            nuevo_estado = problema.resultado(self.estado, accion)
            if nuevo_estado is not None:
                nuevo_nodo = Nodo(nuevo_estado, accion, self.acciones, self)
                self.hijos.append(nuevo_nodo)
        return self.hijos


# %% Búsqueda en Profundidad (DFS)
def dfs(problema, nodo_actual, visitados, camino):
    if problema.es_objetivo(nodo_actual.estado):
        return camino + [nodo_actual]

    visitados.add(nodo_actual.estado)

    for hijo in nodo_actual.expandir(problema):
        if hijo.estado not in visitados:
            resultado = dfs(problema, hijo, visitados, camino + [nodo_actual])
            if resultado is not None:
                return resultado

    return None


# %% Visualización del Laberinto y el Camino
def visualizar_laberinto(laberinto, camino):
    # Convertir el laberinto a una matriz NumPy
    laberinto_np = np.array(laberinto)

    # Crear un mapa de colores personalizado
    # 0: Pared (negro), 1: Camino (blanco), 2: Agua (azul), 3: Arena (amarillo), 4: Bosque (verde), 5: Montaña (gris)
    colores = ['black', 'white', 'blue', 'yellow', 'green', 'gray']
    cmap = ListedColormap(colores)

    # Crear una figura y un eje
    fig, ax = plt.subplots()

    # Mostrar el laberinto con el mapa de colores personalizado
    ax.imshow(laberinto_np, cmap=cmap, interpolation='none')

    # Dibujar el camino
    if camino:
        camino_filas = [nodo.estado.fila for nodo in camino]
        camino_columnas = [nodo.estado.columna for nodo in camino]
        ax.plot(camino_columnas, camino_filas, marker='o', color='red', linewidth=2, markersize=10)

    # Configurar el eje
    ax.set_xticks(range(len(laberinto[0])))
    ax.set_yticks(range(len(laberinto)))
    ax.grid(which='both', color='black', linestyle='-', linewidth=1)

    # Mostrar la figura
    plt.show()


# %% Definiciones
if __name__ == '__main__':
    # Cargar el laberinto desde el archivo
    laberinto = np.loadtxt("map.txt", delimiter=',', dtype=int)

    # Definir acciones
    arriba = Accion('arriba')
    abajo = Accion('abajo')
    izquierda = Accion('izquierda')
    derecha = Accion('derecha')
    acciones = [arriba, abajo, izquierda, derecha]

    # Definir estados inicial y objetivo

    print("Por favor, ingresa la fila del estado inicial y la columna del estado inicial")
    estado_inicial_fila = int(input("Fila inicial: "))
    estado_inicial_columna = int(input("Columna inicial: "))
    print("Ahora, ingresa la fila y columna del estado objetivo")
    estado_objetivo_fila = int(input("Fila objetivo: "))
    estado_objetivo_columna = int(input("Columna objetivo: "))


    estado_inicial = Estado(estado_inicial_fila, estado_inicial_columna)  # Fila 10, Columna 1 (índices base 0)
    estados_objetivos = [Estado(estado_objetivo_fila,estado_objetivo_columna)]  # Fila 9, Columna 9 (índices base 0)

    # Crear el problema
    problema_laberinto = Problema(estado_inicial, estados_objetivos, laberinto)

    # Crear el nodo inicial
    nodo_inicial = Nodo(estado_inicial, None, acciones)

    # Realizar la búsqueda en profundidad (DFS)
    visitados = set()
    camino = dfs(problema_laberinto, nodo_inicial, visitados, [])

    # Mostrar el camino encontrado
    if camino:
        print("Camino encontrado:")
        for nodo in camino:
            print(f"Estado: {nodo.estado}, Acción: {nodo.accion}")

        # Visualizar el laberinto y el camino
        visualizar_laberinto(laberinto, camino)
    else:
        print("No se encontró un camino al objetivo.")