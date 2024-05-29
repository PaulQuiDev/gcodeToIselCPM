import matplotlib
matplotlib.use('TkAgg')  # Force l'utilisation de Tkinter comme backend
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import threading
import queue
import time

# Fonction pour lire les données à partir du fichier de logs
def read_log_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        points = []
        for line in lines[1:]:  # Ignorer la première ligne (en-tête)
            parts = line.strip().split(',')
            x = float(parts[0].split('X')[1])
            y = float(parts[1].split('Y')[1])
            z = float(parts[2].split('Z')[1])
            points.append((x, y, z))
        return points

# Fonction pour mettre à jour le tracé en 3D
def update_plot(ax, all_points, new_points):
    ax.clear()
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Points de déplacement de la CNC')
    if all_points:
        xs, ys, zs = zip(*all_points)
        ax.scatter(xs, ys, zs, color='b', marker='o', label='All Points')
    if new_points:
        xs, ys, zs = zip(*new_points)
        ax.scatter(xs, ys, zs, color='r', marker='o', label='New Points')
    if all_points or new_points:
        ax.legend()
    fig.canvas.draw_idle()

# Fonction pour la lecture en arrière-plan
def read_thread(q):
    all_points = set()
    while True:
        current_points = set(read_log_file('cnc_logs.txt'))
        new_points = current_points - all_points
        removed_points = all_points - current_points
        all_points = current_points
        q.put((list(all_points), list(new_points)))
        time.sleep(0.5)  # Pause d'une seconde avant de mettre à jour à nouveau

# Création du tracé initial
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Création de la queue
q = queue.Queue()

# Lancement du thread de lecture
thread = threading.Thread(target=read_thread, args=(q,))
thread.daemon = True
thread.start()

# Boucle principale pour mettre à jour le tracé
def main_loop():
    if not q.empty():
        all_points, new_points = q.get()
        update_plot(ax, all_points, new_points)
    fig.canvas.get_tk_widget().after(100, main_loop)

# Démarrer la boucle principale
fig.canvas.get_tk_widget().after(100, main_loop)
plt.show()
