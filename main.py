import pygame
import numpy as np
import sys
from collections import defaultdict

# Inicializar pygame
pygame.init()


# %% Acción
class Accion:
    def __init__(self, nombre):
        self.nombre = nombre

    def __str__(self):
        return self.nombre


# %% Estado
class Estado:
    def __init__(self, fila, columna, direccion='derecha'):
        self.fila = fila
        self.columna = columna
        self.direccion = direccion  # 'arriba', 'abajo', 'izquierda', 'derecha'

    def __str__(self):
        return f"({self.fila}, {self.columna}, {self.direccion})"

    def __eq__(self, otro):
        return self.fila == otro.fila and self.columna == otro.columna and self.direccion == otro.direccion

    def __hash__(self):
        return hash((self.fila, self.columna, self.direccion))


# %% Clase Agente
class Agente:
    def __init__(self, nombre, habilidades):
        """
        habilidades: dict con:
        - 'puede_girar_izquierda': bool
        - 'puede_girar_derecha': bool
        - 'vision_lejana': bool (si puede ver más allá de la celda actual al sensar)
        - 'rango_movimiento': int (cuántas celdas puede avanzar de una vez)
        - 'vision_omni': bool (nueva habilidad para ver en todas direcciones)
        """
        self.nombre = nombre
        self.habilidades = habilidades
        self.historial = []
        self.camino_visitado = set()
        self.puntos_decision = set()
        self.vision_omni_activada = False
        self.cooldown_omni = 0
        self.duracion_omni = 3  # Turnos que dura la visión omni

    def puede_realizar_accion(self, accion):
        if accion.nombre == 'girar_izquierda':
            return self.habilidades.get('puede_girar_izquierda', True)
        elif accion.nombre == 'girar_derecha':
            return self.habilidades.get('puede_girar_derecha', True)
        return True

    def registrar_decision(self, estado, accion, resultado):
        self.historial.append({
            'estado': estado,
            'accion': accion,
            'resultado': resultado
        })
        self.camino_visitado.add((estado.fila, estado.columna))

        # Si hay múltiples acciones posibles, es punto de decisión
        if len([a for a in ['avanzar', 'girar_izquierda', 'girar_derecha']
                if self.puede_realizar_accion(Accion(a))]) > 1:
            self.puntos_decision.add((estado.fila, estado.columna))


# %% Problema
class Problema:
    def __init__(self, estado_inicial, estados_objetivos, laberinto, agente):
        self.estado_inicial = estado_inicial
        self.estados_objetivos = estados_objetivos
        self.laberinto = laberinto
        self.agente = agente
        self.mapa_visible = np.zeros_like(laberinto)
        self.mapa_visible[estado_inicial.fila][estado_inicial.columna] = 1

    def es_objetivo(self, estado):
        return estado in self.estados_objetivos

    def sensar_camino(self, estado):
        """Sensar si hay camino en la dirección actual según las habilidades del agente"""
        fila, columna = estado.fila, estado.columna

        # Revelar según habilidades del agente
        if self.agente.vision_omni_activada:
            # Visión omni-direccional (todas direcciones)
            direcciones = ['arriba', 'abajo', 'izquierda', 'derecha']
            alcance = 3

            for direccion in direcciones:
                for i in range(1, alcance + 1):
                    if direccion == "arriba":
                        f, c = fila - i, columna
                    elif direccion == "abajo":
                        f, c = fila + i, columna
                    elif direccion == "izquierda":
                        f, c = fila, columna - i
                    elif direccion == "derecha":
                        f, c = fila, columna + i

                    if 0 <= f < len(self.laberinto) and 0 <= c < len(self.laberinto[0]):
                        self.mapa_visible[f][c] = 1
                        if self.laberinto[f][c] in [0, 5]:  # Si es pared o montaña
                            break

            # Desactivar después de usar
            self.agente.vision_omni_activada = False
            self.agente.cooldown_omni = 5  # 5 turnos de cooldown

        elif self.agente.habilidades.get('vision_lejana', False):
            # Visión de largo alcance (3 celdas)
            for i in range(1, 4):
                if estado.direccion == "arriba":
                    f, c = fila - i, columna
                elif estado.direccion == "abajo":
                    f, c = fila + i, columna
                elif estado.direccion == "izquierda":
                    f, c = fila, columna - i
                elif estado.direccion == "derecha":
                    f, c = fila, columna + i

                if 0 <= f < len(self.laberinto) and 0 <= c < len(self.laberinto[0]):
                    self.mapa_visible[f][c] = 1
                    if self.laberinto[f][c] in [0, 5]:  # Si es pared o montaña
                        break
        else:
            # Visión normal (solo celda frontal)
            if estado.direccion == "arriba":
                f, c = fila - 1, columna
            elif estado.direccion == "abajo":
                f, c = fila + 1, columna
            elif estado.direccion == "izquierda":
                f, c = fila, columna - 1
            elif estado.direccion == "derecha":
                f, c = fila, columna + 1

            if 0 <= f < len(self.laberinto) and 0 <= c < len(self.laberinto[0]):
                self.mapa_visible[f][c] = 1

        # Verificar si la celda frontal es transitable
        if estado.direccion == "arriba":
            nueva_fila, nueva_columna = fila - 1, columna
        elif estado.direccion == "abajo":
            nueva_fila, nueva_columna = fila + 1, columna
        elif estado.direccion == "izquierda":
            nueva_fila, nueva_columna = fila, columna - 1
        elif estado.direccion == "derecha":
            nueva_fila, nueva_columna = fila, columna + 1

        if (0 <= nueva_fila < len(self.laberinto) and 0 <= nueva_columna < len(self.laberinto[0])
                and self.laberinto[nueva_fila][nueva_columna] != 0  # Pared
                and self.laberinto[nueva_fila][nueva_columna] != 5  # Montaña
        ):
            return True
        return False

    def avanzar(self, estado):
        """Avanzar en la dirección actual según habilidades del agente"""
        fila, columna = estado.fila, estado.columna
        rango = self.agente.habilidades.get('rango_movimiento', 1)

        for paso in range(1, rango + 1):
            if estado.direccion == "arriba":
                nueva_fila, nueva_columna = fila - paso, columna
            elif estado.direccion == "abajo":
                nueva_fila, nueva_columna = fila + paso, columna
            elif estado.direccion == "izquierda":
                nueva_fila, nueva_columna = fila, columna - paso
            elif estado.direccion == "derecha":
                nueva_fila, nueva_columna = fila, columna + paso

            # Verificar si la nueva posición es válida
            if not (0 <= nueva_fila < len(self.laberinto)
                    and 0 <= nueva_columna < len(self.laberinto[0])
                    and self.laberinto[nueva_fila][nueva_columna] != 0  # Pared
                    and self.laberinto[nueva_fila][nueva_columna] != 5  # Montaña
            ):
                if paso == 1:
                    return None  # No se pudo mover
                break  # Para movimiento de múltiples pasos

            # Actualizar posición si este paso es válido
            fila, columna = nueva_fila, nueva_columna

        # Revelar solo la celda final
        self.mapa_visible[fila][columna] = 1
        return Estado(fila, columna, estado.direccion)

    def girar_izquierda(self, estado):
        """Girar 90 grados a la izquierda si el agente puede"""
        if not self.agente.puede_realizar_accion(Accion('girar_izquierda')):
            return None

        direcciones = ['arriba', 'izquierda', 'abajo', 'derecha']
        current_idx = direcciones.index(estado.direccion)
        nueva_direccion = direcciones[(current_idx + 1) % 4]
        return Estado(estado.fila, estado.columna, nueva_direccion)

    def girar_derecha(self, estado):
        """Girar 90 grados a la derecha si el agente puede"""
        if not self.agente.puede_realizar_accion(Accion('girar_derecha')):
            return None

        direcciones = ['arriba', 'derecha', 'abajo', 'izquierda']
        current_idx = direcciones.index(estado.direccion)
        nueva_direccion = direcciones[(current_idx + 1) % 4]
        return Estado(estado.fila, estado.columna, nueva_direccion)


# %% Visualización con Pygame
def visualizar_laberinto_pygame(laberinto, estado_actual, problema, screen, font, cell_size=40):
    # Colores
    COLORES = {
        0: (0, 0, 0),  # Pared - negro
        1: (255, 255, 255),  # Camino - blanco
        2: (0, 0, 255),  # Agua - azul
        3: (255, 255, 0),  # Arena - amarillo
        4: (0, 128, 0),  # Bosque - verde oscuro
        5: (128, 128, 128),  # Montaña - gris
        'oculto': (50, 50, 50),  # Área no explorada - gris oscuro
        'agente': (255, 0, 0),  # Agente - rojo
        'objetivo': (0, 255, 0),  # Objetivo - verde
        'visitado': (200, 200, 255),  # Camino visitado - azul claro
        'decision': (255, 165, 0)  # Punto de decisión - naranja
    }

    # Dibujar el laberinto
    for fila in range(len(laberinto)):
        for columna in range(len(laberinto[0])):
            rect = pygame.Rect(columna * cell_size, fila * cell_size, cell_size, cell_size)

            if problema.mapa_visible[fila][columna]:
                # Celda explorada
                if (fila, columna) in problema.agente.camino_visitado:
                    # Celda visitada
                    pygame.draw.rect(screen, COLORES['visitado'], rect)
                elif laberinto[fila][columna] in [0, 5]:  # Pared o montaña
                    pygame.draw.rect(screen, COLORES[laberinto[fila][columna]], rect)
                else:
                    pygame.draw.rect(screen, COLORES[laberinto[fila][columna]], rect)

                # Marcar puntos de decisión
                if (fila, columna) in problema.agente.puntos_decision:
                    pygame.draw.circle(screen, COLORES['decision'],
                                       (columna * cell_size + cell_size // 2, fila * cell_size + cell_size // 2),
                                       cell_size // 4)

                pygame.draw.rect(screen, (0, 0, 0), rect, 1)  # Borde
            else:
                # Celda no explorada
                pygame.draw.rect(screen, COLORES['oculto'], rect)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)  # Borde

    # Dibujar el objetivo (solo si está visible)
    objetivo = problema.estados_objetivos[0]
    if problema.mapa_visible[objetivo.fila][objetivo.columna]:
        rect = pygame.Rect(objetivo.columna * cell_size, objetivo.fila * cell_size, cell_size, cell_size)
        pygame.draw.rect(screen, COLORES['objetivo'], rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1)

    # Dibujar el agente
    agente_rect = pygame.Rect(
        estado_actual.columna * cell_size + cell_size // 4,
        estado_actual.fila * cell_size + cell_size // 4,
        cell_size // 2,
        cell_size // 2
    )
    pygame.draw.rect(screen, COLORES['agente'], agente_rect)

    # Dibujar la dirección del agente
    centro_x = estado_actual.columna * cell_size + cell_size // 2
    centro_y = estado_actual.fila * cell_size + cell_size // 2

    if estado_actual.direccion == "arriba":
        puntos = [
            (centro_x, centro_y - cell_size // 4),
            (centro_x - cell_size // 4, centro_y + cell_size // 4),
            (centro_x + cell_size // 4, centro_y + cell_size // 4)
        ]
    elif estado_actual.direccion == "abajo":
        puntos = [
            (centro_x, centro_y + cell_size // 4),
            (centro_x - cell_size // 4, centro_y - cell_size // 4),
            (centro_x + cell_size // 4, centro_y - cell_size // 4)
        ]
    elif estado_actual.direccion == "izquierda":
        puntos = [
            (centro_x - cell_size // 4, centro_y),
            (centro_x + cell_size // 4, centro_y - cell_size // 4),
            (centro_x + cell_size // 4, centro_y + cell_size // 4)
        ]
    elif estado_actual.direccion == "derecha":
        puntos = [
            (centro_x + cell_size // 4, centro_y),
            (centro_x - cell_size // 4, centro_y - cell_size // 4),
            (centro_x - cell_size // 4, centro_y + cell_size // 4)
        ]

    pygame.draw.polygon(screen, (0, 0, 0), puntos)

    # Mostrar información
    info_text = f"Posición: ({estado_actual.fila}, {estado_actual.columna}) | Dirección: {estado_actual.direccion}"
    text_surface = font.render(info_text, True, (255, 255, 255))
    screen.blit(text_surface, (10, len(laberinto) * cell_size + 10))

    # Mostrar estado de la visión omni
    omni_status = ""
    if 'vision_omni' in problema.agente.habilidades and problema.agente.habilidades['vision_omni']:
        if problema.agente.vision_omni_activada:
            omni_status = " (OMNI ACTIVA)"
        elif problema.agente.cooldown_omni > 0:
            omni_status = f" (Cooldown: {problema.agente.cooldown_omni})"

    agente_info = f"Agente: {problema.agente.nombre} | Habilidades: {problema.agente.habilidades}{omni_status}"
    agente_surface = font.render(agente_info, True, (255, 255, 255))
    screen.blit(agente_surface, (10, len(laberinto) * cell_size + 40))

    instrucciones = "Flechas: Moverse | Espacio: Sensar | R: Reiniciar | ESC: Salir | T: Ver Recorrido | O: Visión Omni"
    instrucciones_surface = font.render(instrucciones, True, (255, 255, 255))
    screen.blit(instrucciones_surface, (10, len(laberinto) * cell_size + 70))


# %% Mostrar árbol de decisiones
def mostrar_arbol_decisiones(agente, font, screen, width, height):
    screen.fill((0, 0, 0))
    y_pos = 50

    titulo = font.render("Recorrido del agente", True, (255, 255, 255))
    screen.blit(titulo, (width // 2 - titulo.get_width() // 2, 20))

    for i, decision in enumerate(agente.historial):
        texto = f"{i + 1}. En {decision['estado']} -> {decision['accion']} -> {decision['resultado']}"
        texto_surface = font.render(texto, True, (255, 255, 255))
        screen.blit(texto_surface, (50, y_pos))
        y_pos += 30

        if y_pos > height - 50:
            texto_continuar = font.render("Presione cualquier tecla para continuar...", True, (255, 255, 255))
            screen.blit(texto_continuar, (width // 2 - texto_continuar.get_width() // 2, height - 30))
            pygame.display.flip()
            esperar_tecla()
            screen.fill((0, 0, 0))
            y_pos = 50
            titulo = font.render("Árbol de Decisiones del Agente (cont.)", True, (255, 255, 255))
            screen.blit(titulo, (width // 2 - titulo.get_width() // 2, 20))

    texto_final = font.render("Presione cualquier tecla para volver al juego...", True, (255, 255, 255))
    screen.blit(texto_final, (width // 2 - texto_final.get_width() // 2, height - 30))
    pygame.display.flip()
    esperar_tecla()


def esperar_tecla():
    esperando = True
    while esperando:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                esperando = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                esperando = False


# %% Juego principal
def jugar_laberinto_pygame(laberinto, estado_inicial, estado_objetivo, agente):
    # Configuración de Pygame
    cell_size = 40
    width = len(laberinto[0]) * cell_size
    height = len(laberinto) * cell_size + 100  # Espacio adicional para texto

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(f"Laberinto con Agente: {agente.nombre}")
    font = pygame.font.SysFont(None, 24)

    problema = Problema(estado_inicial, [estado_objetivo], laberinto, agente)
    estado_actual = estado_inicial

    clock = pygame.time.Clock()
    running = True

    while running:
        # Actualizar cooldown de habilidades
        if agente.cooldown_omni > 0:
            agente.cooldown_omni -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Reiniciar el juego
                    problema = Problema(estado_inicial, [estado_objetivo], laberinto, agente)
                    estado_actual = estado_inicial
                    agente.vision_omni_activada = False
                    agente.cooldown_omni = 0
                elif event.key == pygame.K_t:
                    # Mostrar árbol de decisiones
                    mostrar_arbol_decisiones(agente, font, screen, width, height)
                elif event.key == pygame.K_UP:
                    nuevo_estado = problema.avanzar(estado_actual)
                    if nuevo_estado:
                        agente.registrar_decision(estado_actual, Accion('avanzar'), nuevo_estado)
                        estado_actual = nuevo_estado
                elif event.key == pygame.K_LEFT:
                    nuevo_estado = problema.girar_izquierda(estado_actual)
                    if nuevo_estado:
                        agente.registrar_decision(estado_actual, Accion('girar_izquierda'), nuevo_estado)
                        estado_actual = nuevo_estado
                elif event.key == pygame.K_RIGHT:
                    nuevo_estado = problema.girar_derecha(estado_actual)
                    if nuevo_estado:
                        agente.registrar_decision(estado_actual, Accion('girar_derecha'), nuevo_estado)
                        estado_actual = nuevo_estado
                elif event.key == pygame.K_SPACE:
                    resultado = problema.sensar_camino(estado_actual)
                    agente.registrar_decision(estado_actual, Accion('sensar'),
                                              "Camino libre" if resultado else "Obstáculo detectado")
                elif event.key == pygame.K_o:  # Tecla 'O' para activar visión omni
                    if (agente.habilidades.get('vision_omni', False) and
                            agente.cooldown_omni == 0 and
                            not agente.vision_omni_activada):
                        agente.vision_omni_activada = True
                        problema.sensar_camino(estado_actual)  # Forzar sensado inmediato

        # Verificar si se alcanzó el objetivo
        if problema.es_objetivo(estado_actual):
            screen.fill((0, 0, 0))
            win_text = f"¡{agente.nombre} ha llegado al objetivo!"
            text_surface = font.render(win_text, True, (255, 255, 255))
            screen.blit(text_surface, (width // 2 - text_surface.get_width() // 2, height // 2))

            stats_text = f"Celdas visitadas: {len(agente.camino_visitado)} | Decisiones tomadas: {len(agente.historial)}"
            stats_surface = font.render(stats_text, True, (255, 255, 255))
            screen.blit(stats_surface, (width // 2 - stats_surface.get_width() // 2, height // 2 + 40))

            pygame.display.flip()
            pygame.time.wait(3000)
            running = False

        # Dibujar
        screen.fill((0, 0, 0))
        visualizar_laberinto_pygame(laberinto, estado_actual, problema, screen, font, cell_size)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


def solicitar_posicion_valida(laberinto, mensaje):
    while True:
        try:
            fila = int(input(f"Ingrese la fila para {mensaje}: "))
            columna = int(input(f"Ingrese la columna para {mensaje}: "))

            if 0 <= fila < len(laberinto) and 0 <= columna < len(laberinto[0]):
                if laberinto[fila][columna] != 0:  # No es pared
                    return fila, columna
                else:
                    print("Error: No puedes colocar esta posición en una pared.")
            else:
                print("Error: Posición fuera de los límites del laberinto.")
        except ValueError:
            print("Error: Ingrese números enteros válidos.")


# %% Main
if __name__ == '__main__':
    # Cargar el laberinto desde el archivo
    try:
        laberinto = np.loadtxt("map.txt", delimiter=',', dtype=int)
    except:
        # Si no hay archivo, crear un laberinto de ejemplo
        laberinto = np.array([
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 1, 1, 1, 1, 1],
            [1, 0, 1, 0, 1, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ])

    # Definir estados inicial y objetivo
    estado_inicial_fila, estado_inicial_columna = solicitar_posicion_valida(laberinto, "el estado inicial")
    estado_objetivo_fila, estado_objetivo_columna = solicitar_posicion_valida(laberinto, "el estado objetivo")

    # Validar que el estado objetivo no sea una pared
    if laberinto[estado_objetivo_fila][estado_objetivo_columna] == 0:
        print("Error: El estado objetivo no puede estar en una pared.")
        sys.exit(1)

    estado_inicial = Estado(estado_inicial_fila, estado_inicial_columna, 'derecha')
    estado_objetivo = Estado(estado_objetivo_fila, estado_objetivo_columna)

    # Crear agentes con diferentes habilidades
    print("\nSelecciona el tipo de agente:")
    print("1. Agente básico (movimiento normal)")
    print("2. Agente con visión limitada (no puede girar a la izquierda)")
    print("3. Agente veloz (puede avanzar 2 celdas, pero no sensar)")
    print("4. Agente Omni (visión en todas direcciones)")

    opcion = input("Opción: ")

    if opcion == "2":
        agente = Agente("Explorador Zurdo", {
            'puede_girar_izquierda': False,
            'vision_lejana': False
        })
    elif opcion == "3":
        agente = Agente("Corredor Veloz", {
            'rango_movimiento': 2,
            'vision_lejana': False,
            'puede_sensar': False
        })
    elif opcion == "4":
        agente = Agente("Explorador Omni", {
            'vision_omni': True,
            'vision_lejana': False,
            'puede_girar_izquierda': True,
            'puede_girar_derecha': True,
            'rango_movimiento': 1
        })
    else:
        agente = Agente("Explorador Básico", {
            'vision_lejana': False
        })

    # Iniciar el juego
    jugar_laberinto_pygame(laberinto, estado_inicial, estado_objetivo, agente)