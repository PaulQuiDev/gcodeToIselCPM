import tkinter as tk
from tkinter import ttk, filedialog , messagebox
from PIL import Image, ImageTk
from ClasseCNC import CNC
import threading    
import serial.tools.list_ports
import matplotlib.pyplot as plt 
import subprocess
import platform
import shutil
import os
import sys  


try :
    if  platform.system() == 'Linux': #Laser ready 1:Linux rasp 2:Windows avec ESP 3:False
        try :
            import RPi.GPIO as GPIO # Linux on rasberry pi
            laserReady = 1 
        except:
            laserReady = 2
    elif platform.system() == 'Windows':
        laserReady = 2  
    else :
        laserReady = 0 
except:
    #print("La découpe laser n'est pas disponible.")
    laserReady = 0

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
 
    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, background="yellow", relief="solid", borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def update_text(self, new_text):
        self.text = new_text


class CNCInterface:
    def __init__(self, master):
        self.master = master
        self.master.title("CNC Interface")
        self.master.configure(bg='grey')

        self.move_increment = tk.DoubleVar(value=1)  # Variable pour l'incrément de déplacement
        self.progress = tk.DoubleVar()

        self.stop_event = threading.Event()  # Variable de contrôle pour arrêter le processus

        self.file = None

        self.master.bind("<KeyRelease>", self.on_key_press) # controil clavier triger 

        # Initialisation du laser si prêt
        if laserReady == 1: 
            self.laserPower = -1 # est un flaot pour rasp
            GPIO.setmode(GPIO.BCM)  # Utilisation des numéros de broches BCM
            GPIO.setup(18, GPIO.OUT)  
            self.pwm = GPIO.PWM(18, 4000)
        elif laserReady == 2 :
            self.laserPower = -1
            self.laserCom = None 

        self.load_images()
        self.create_widgets()
        self.setup_grid()
        self.initConnection()  
        self.disable_buttons("(Printer not connected)")

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        
    def create_widgets(self):
        style = ttk.Style()
        style.configure("TButton", background="grey", borderwidth=1, relief="flat")

        self.tooltips = {}
        # Frame pour les boutons de direction
        self.direction_frame = ttk.LabelFrame(self.master, padding="10 10 10 10", text='Contrôle Machine')
        self.direction_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # =======================crois directionnelle
        self.x_minus_button = ttk.Button(self.direction_frame, text="-X", image=self.img_mouvx, command=lambda: self.move("X", -self.move_increment.get()))
        self.x_plus_button = ttk.Button(self.direction_frame, text="+X", image=self.img_mouvX, command=lambda: self.move("X", self.move_increment.get()))
        self.y_minus_button = ttk.Button(self.direction_frame, text="-Y", image=self.img_mouvy, command=lambda: self.move("Y", -self.move_increment.get()))
        self.y_plus_button = ttk.Button(self.direction_frame, text="+Y", image=self.img_mouvY, command=lambda: self.move("Y", self.move_increment.get()))
        self.z_minus_button = ttk.Button(self.direction_frame, text="-Z", image=self.img_mouvz, command=lambda: self.move("Z", self.move_increment.get()))
        self.z_plus_button = ttk.Button(self.direction_frame, text="+Z", image=self.img_mouvZ, command=lambda: self.move("Z", -self.move_increment.get()))
        self.home_button= ttk.Button(self.direction_frame, text="home", image=self.img_home , command=lambda: self.home_machine())

        self.x_minus_button.grid(row=1, column=0, sticky="nsew")
        self.x_plus_button.grid(row=1, column=2, sticky="nsew")
        self.y_minus_button.grid(row=2, column=1, sticky="nsew")
        self.y_plus_button.grid(row=0, column=1, sticky="nsew")
        self.z_minus_button.grid(row=2, column=3, sticky="nsew")
        self.z_plus_button.grid(row=0, column=3, sticky="nsew")
        self.home_button.grid(row=1, column= 1 , sticky='nsew')

        # Frame pour les boutons d'incrément de déplacement avec un titre
        self.increment_frame = ttk.LabelFrame(self.master, text="Incrément de déplacement", padding="10 10 10 10")
        self.increment_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.increment_100mm_button = ttk.Radiobutton(self.increment_frame, text="50 mm", variable=self.move_increment, value=50)
        self.increment_10mm_button = ttk.Radiobutton(self.increment_frame, text="10 mm", variable=self.move_increment, value=10)
        self.increment_5mm_button = ttk.Radiobutton(self.increment_frame, text="1 mm", variable=self.move_increment, value=1)
        self.increment_1mm_button = ttk.Radiobutton(self.increment_frame, text="0.1 mm", variable=self.move_increment, value=0.1)

        self.increment_100mm_button.grid(row=0, column=0, sticky="nsew")
        self.increment_10mm_button.grid(row=0, column=1, sticky="nsew")
        self.increment_5mm_button.grid(row=0, column=2, sticky="nsew")
        self.increment_1mm_button.grid(row=0, column=3, sticky="nsew")

        # Bouton pour définir le point 0 si pas laser juste pt 0 sinon avec laser découpe
        if (laserReady != 0) :
            self.position_laser = ttk.Frame(self.master)
            self.position_laser.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

            self.position_laser.grid_rowconfigure(0, weight=1)
            self.position_laser.grid_columnconfigure(0, weight=1)
            self.position_laser.grid_columnconfigure(1, weight=1)
                
            self.define_button = ttk.Button(self.position_laser, text="Définir Point 0",compound='right', image=self.img_Pt0 ,command=self.define_point)
            self.define_button.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            if (laserReady == 1) :
                self.laserBp = ttk.Button(self.position_laser , text="LASER" ,compound='top', image= self.img_laser, command=self.laserPowerSelect )
                self.laserBp.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
            elif (laserReady == 2 and self.laserCom == None  )  :
                self.laserBp = ttk.Button(self.position_laser , text="LASER Signal" ,compound='top', image= self.img_laser_com, command=self.laserComOpen )
                self.laserBp.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        else :
            self.define_button = ttk.Button(self.master, text="Définir Point 0",compound='right', image=self.img_Pt0 ,command=self.define_point)
            self.define_button.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")


        # Boutons pour charger le fichier et lancer la découpe
        self.load_button = ttk.Button(self.master, text='Charger un Fichier', image=self.img_open, compound='top', command=self.load_file)
        self.load_button.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.start_button = ttk.Button(self.master, text="Lancer la découpe", image=self.img_start, compound='left' ,command=self.start_cut)
        self.start_button.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Frame pour les boutons de démarrage et d'arrêt de l'outil
        self.tool_control_frame = ttk.Frame(self.master)
        self.tool_control_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        # Configure rows and columns in the tool_control_frame to expand
        self.tool_control_frame.grid_rowconfigure(0, weight=1)
        self.tool_control_frame.grid_columnconfigure(0, weight=1)
        self.tool_control_frame.grid_columnconfigure(1, weight=1)

        # Boutons pour démarrer et arrêter l'outil
        self.start_tool_button = ttk.Button(self.tool_control_frame, text="Démarrer l'outil" , image=self.img_toolStart,compound='bottom' ,command=self.start_tool)
        self.start_tool_button.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.stop_tool_button = ttk.Button(self.tool_control_frame, text="Arrêter l'outil",image=self.img_toolStop, compound='bottom' , command=self.stop_tool)
        self.stop_tool_button.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Zone de texte pour afficher les messages
        self.message_text = tk.Text(self.master, height=10)
        self.message_text.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Barre de progression
        self.progress_bar = ttk.Progressbar(self.master, orient=tk.HORIZONTAL, length=200, mode='determinate', variable=self.progress)
        self.progress_bar.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Boutons d'arrêt et de connexion
        style = ttk.Style()
        style.configure("Stop.TButton",
                foreground="black",    # Couleur du texte
                background="red",      # Couleur de fond
                padding=10,           # Remplissage (optionnel)
                font=("Helvetica", 12, "bold"))  # Police (optionnel)
        
        self.stop_button = ttk.Button(self.master, text="Arrêt STOP", command=self.stop  , style="Stop.TButton")
        self.stop_button.grid(row=5, column=0, padx=10, pady=10, sticky="nsew")

        self.connect_button = ttk.Button(self.master, text="Connexion", command=self.connect)
        self.connect_button.grid(row=5, column=1, padx=10, pady=10, sticky="nsew")

        self.tooltips[self.x_minus_button] = Tooltip(self.x_minus_button, "-X")
        self.tooltips[self.x_plus_button] = Tooltip(self.x_plus_button, "+X")
        self.tooltips[self.y_minus_button] = Tooltip(self.y_minus_button, "-Y")
        self.tooltips[self.y_plus_button] = Tooltip(self.y_plus_button, "+Y")
        self.tooltips[self.z_minus_button] = Tooltip(self.z_minus_button, "-Z")
        self.tooltips[self.z_plus_button] = Tooltip(self.z_plus_button, "+Z")
        self.tooltips[self.home_button] = Tooltip(self.home_button, "Home")
        self.tooltips[self.increment_100mm_button] = Tooltip(self.increment_100mm_button, "50 mm")
        self.tooltips[self.increment_10mm_button] = Tooltip(self.increment_10mm_button, "10 mm")
        self.tooltips[self.increment_5mm_button] = Tooltip(self.increment_5mm_button, "1 mm")
        self.tooltips[self.increment_1mm_button] = Tooltip(self.increment_1mm_button, "0.1 mm trop petit pour Z")
        self.tooltips[self.define_button] = Tooltip(self.define_button, "Set Point 0")
        self.tooltips[self.load_button] = Tooltip(self.load_button, "Load File")
        self.tooltips[self.start_button] = Tooltip(self.start_button, "Start Cut")
        self.tooltips[self.start_tool_button] = Tooltip(self.start_tool_button, "Start Tool")
        self.tooltips[self.stop_tool_button] = Tooltip(self.stop_tool_button, "Stop Tool")
        self.tooltips[self.stop_button] = Tooltip(self.stop_button, "Stop")

    def disable_buttons(self,message :str):
        self.x_minus_button.state(['disabled'])
        self.x_plus_button.state(['disabled'])
        self.y_minus_button.state(['disabled'])
        self.y_plus_button.state(['disabled'])
        self.z_minus_button.state(['disabled'])
        self.z_plus_button.state(['disabled'])
        self.home_button.state(['disabled'])
        self.increment_100mm_button.state(['disabled'])
        self.increment_10mm_button.state(['disabled'])
        self.increment_5mm_button.state(['disabled'])
        self.increment_1mm_button.state(['disabled'])
        self.define_button.state(['disabled'])
        self.load_button.state(['disabled'])
        self.start_button.state(['disabled'])
        self.start_tool_button.state(['disabled'])
        self.stop_tool_button.state(['disabled'])

        if (laserReady == 1 or laserReady == 2):
            self.laserBp.state(['disabled'])
    
        # Mettre à jour les infobulles pour indiquer que l'imprimante n'est pas connectée
        self.tooltips[self.x_minus_button].update_text("-X \n" + message)
        self.tooltips[self.x_plus_button].update_text("+X \n" + message)
        self.tooltips[self.y_minus_button].update_text("-Y \n" + message)
        self.tooltips[self.y_plus_button].update_text("+Y \n" + message)
        self.tooltips[self.z_minus_button].update_text("-Z \n" + message)
        self.tooltips[self.z_plus_button].update_text("+Z \n" + message)
        self.tooltips[self.home_button].update_text("Home \n" + message)
        self.tooltips[self.increment_100mm_button].update_text("100 mm \n" + message)
        self.tooltips[self.increment_10mm_button].update_text("10 mm \n" + message)
        self.tooltips[self.increment_5mm_button].update_text("5 mm \n" + message)
        self.tooltips[self.increment_1mm_button].update_text("1 mm \n" + message)
        self.tooltips[self.define_button].update_text("Set Point 0 \n" + message)
        self.tooltips[self.load_button].update_text("Load File \n" + message)
        self.tooltips[self.start_button].update_text("Start Cut \n" + message)
        self.tooltips[self.start_tool_button].update_text("Start Tool \n" + message)
        self.tooltips[self.stop_tool_button].update_text("Stop Tool \n" + message)

    def enable_buttons(self):
        self.x_minus_button.state(['!disabled'])
        self.x_plus_button.state(['!disabled'])
        self.y_minus_button.state(['!disabled'])
        self.y_plus_button.state(['!disabled'])
        self.z_minus_button.state(['!disabled'])
        self.z_plus_button.state(['!disabled'])
        self.home_button.state(['!disabled'])
        self.increment_100mm_button.state(['!disabled'])
        self.increment_10mm_button.state(['!disabled'])
        self.increment_5mm_button.state(['!disabled'])
        self.increment_1mm_button.state(['!disabled'])
        self.define_button.state(['!disabled'])
        self.load_button.state(['!disabled'])
        self.start_button.state(['!disabled'])
        self.start_tool_button.state(['!disabled'])
        self.stop_tool_button.state(['!disabled'])
        self.stop_button.state(['!disabled'])

        if (laserReady == 1 or laserReady == 2):
            self.laserBp.state(['!disabled'])

        # Restaurer les infobulles originales
        self.tooltips[self.x_minus_button].update_text("-X")
        self.tooltips[self.x_plus_button].update_text("+X")
        self.tooltips[self.y_minus_button].update_text("-Y")
        self.tooltips[self.y_plus_button].update_text("+Y")
        self.tooltips[self.z_minus_button].update_text("-Z")
        self.tooltips[self.z_plus_button].update_text("+Z")
        self.tooltips[self.home_button].update_text("Home")
        self.tooltips[self.increment_100mm_button].update_text("100 mm")
        self.tooltips[self.increment_10mm_button].update_text("10 mm")
        self.tooltips[self.increment_5mm_button].update_text("5 mm")
        self.tooltips[self.increment_1mm_button].update_text("1 mm")
        self.tooltips[self.define_button].update_text("Set Point 0")
        self.tooltips[self.load_button].update_text("Load File")
        self.tooltips[self.start_button].update_text("Start Cut")
        self.tooltips[self.start_tool_button].update_text("Start Tool")
        self.tooltips[self.stop_tool_button].update_text("Stop Tool")
        self.tooltips[self.stop_button].update_text("Stop")
 
    def setup_grid(self):
        for i in range(6):  # Changed from 7 to 6 because we placed tool control buttons in the same row
            self.master.grid_rowconfigure(i, weight=1)
        for i in range(2):
            self.master.grid_columnconfigure(i, weight=1)

        for i in range(4):
            self.direction_frame.grid_rowconfigure(i, weight=1)
            self.direction_frame.grid_columnconfigure(i, weight=1)
        
        for i in range(4):
            self.increment_frame.grid_rowconfigure(0, weight=1)
            self.increment_frame.grid_columnconfigure(i, weight=1)

    def load_images(self):
        # Détermine le chemin de base des ressources (images)
        if hasattr(sys, '_MEIPASS'):
            base_path = os.path.join(sys._MEIPASS, 'img')
        else:
            base_path = os.path.join(os.path.dirname(__file__), 'img')

        # Charger les images pour les boutons de direction
        self.img_open = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "open.png")).resize((150, 150)))
        self.img_start = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "start.png")).resize((90, 50)))
        self.img_mouvY = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "mouv.png")).resize((50, 50)))
        self.img_mouvy = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "mouv.png")).resize((50, 50)).rotate(180))
        self.img_mouvx = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "mouv.png")).resize((50, 50)).rotate(90))
        self.img_mouvX = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "mouv.png")).resize((50, 50)).rotate(270))
        self.img_mouvZ = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "mouvZ.png")).resize((80, 80)))
        self.img_mouvz = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "mouvZ.png")).resize((80, 80)).rotate(180))
        self.img_toolStart = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "outilS.png")).resize((40, 40)))
        self.img_toolStop = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "outilO.png")).resize((40, 40)))
        self.img_home = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "home.png")).resize((50, 50)))
        self.img_Pt0 = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "spot0.png")).resize((50, 50)))
        self.img_visu = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "Visu.png")).resize((50, 50)))
        self.img_laser = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "laser.png")).resize((50, 50)))
        self.img_power_laser = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "PowerLaser.png")))
        self.img_laser_com = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "ComBord.png")).resize((50, 50)))
        self.img_laser_Select = Image.open(os.path.join(base_path, "FQLase.png"))

    def move(self,  axis : str , amount: float):
        message = ""
        amount = int(amount*40)
        if(axis == "X"): 
            message = self.briot.move_x(amount)
        elif( axis == "Y"):
            message = self.briot.move_y(amount)
        elif(axis == "Z"):
            message = self.briot.move_Z(amount//10) # pour raison de sécu
        else:
            message= "Move not understood"

        self.message_text.insert(tk.END, f"Move {axis} by {amount} statu : {message}\n")
        self.message_text.see(tk.END)

    def define_point(self):
        if (self.briot.x == 0 and self.briot.y == 0 and self.briot.z == 0): # if 0 realod old 0 point on log file
            try :
                with open (self.briot.log_file, 'r') as fil:
                    origine = fil.readline()
                origine = origine.split(' ')
                x = int(float(origine[1][1:]))
                y = int(float(origine[2][1:]))
                z = int(float(origine[3][1:]))
                self.briot.go_to_machin(x,y,z)
                self.briot.SetLocal0()
            except:
                print("error no history of position")
        self.briot.SetLocal0()
        self.message_text.insert(tk.END, f"Point 0 défini at X:{self.briot.x} Y:{self.briot.y} Z:{self.briot.z} \n")
        self.message_text.see(tk.END)

    def parse_plot_gcode(self ,gcode_lines):
        x, y, z = 0, 0, 0
        points_g0 = []
        points_g1 = []
        points_arc = []

        for line in gcode_lines:
            line = line.strip()
            if line.startswith('G'):
                parts = line.split()
                command = parts[0]
                new_x, new_y, new_z = x, y, z
                i, j = 0, 0

                for part in parts[1:]:
                    if part.startswith('X'):
                        new_x = float(part[1:])
                    elif part.startswith('Y'):
                        new_y = float(part[1:])
                    elif part.startswith('Z'):
                        new_z = float(part[1:])
                    elif part.startswith('I'):
                        i = float(part[1:])
                    elif part.startswith('J'):
                        j = float(part[1:])

                if ( command == 'G0' or command=='G00'):
                    points_g0.append((new_x, new_y, new_z))
                elif ( command == 'G1' or command =='G01'):
                    points_g1.append((new_x, new_y, new_z))
                elif command in ('G2', 'G02', 'G3', 'G03'):
                    arc_points = self.briot.generate_arc_Z(x, y, z, new_x, new_y, new_z, i, j, command in ('G2', 'G02'),points_per_unit=1)
                    points_arc.extend(arc_points)

                x, y, z = new_x, new_y, new_z

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        if points_g0:
            x_g0, y_g0, z_g0 = zip(*points_g0)
            ax.plot(x_g0, y_g0, z_g0, label='G0 speed Moves', color='red', linestyle=':')
        else:
            print("No G0 commands found.")

        if points_g1:
            x_g1, y_g1, z_g1 = zip(*points_g1)
            ax.plot(x_g1, y_g1, z_g1, label='G1 Moves', color='blue', linestyle='--')
        else:
            print("No G1 commands found.")
        if points_arc:
            x_arc, y_arc , z_arc = zip(*points_arc)
            ax.plot(x_arc,y_arc,z_arc, label='Arc Moves' , color='green', linestyle='-')

        if points_g0 or points_g1:
            ax.set_xlabel('X axis')
            ax.set_ylabel('Y axis')
            ax.set_zlabel('Z axis')
            ax.legend()
            plt.show()
        else:
            print("No G-code commands found to plot.")
            return
    
    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[ ("NetCDF files", "*.nc"),("GCode files", "*.gcode"), ("All files", "*.*")])
        try :
            self.file = self.briot.Read_gcode(file_path) # ne pas faire confiance a l'utilisateur 
            self.parse_plot_gcode(self.file)
        except:
            self.message_text.insert(tk.END, "Erreur Format fichier\n")
            self.message_text.see(tk.END)
        if isinstance(self.file,list) :
            self.message_text.insert(tk.END, f"Fichier chargé: {file_path}\n")
            self.message_text.see(tk.END)
            
            try :
                messagebox.showinfo("Zone travaille","Vérifier que la zone de travaille est bien sur votre piesce")
                self.file = self.briot.generate_order(self.file)
                if (len(self.file) < 2):
                    self.message_text.insert(tk.END, "no order understood\n")
                    self.message_text.see(tk.END)
                    if (len(self.file)==1):
                        self.message_text.insert(tk.END, str(self.file[0]) +"\n")
                        self.message_text.see(tk.END)
                    self.file= None
            except:
                self.file = None
                self.message_text.insert(tk.END, "Error in File\n")
                self.message_text.see(tk.END)

    def start_cut(self):
        if (self.file == None):
            messagebox.showerror("Error File" , "Fichier non charger ou non compris")
        elif (isinstance(self.infoTool,bool) ):
            self.disable_buttons("In prosses")
            self.message_text.insert(tk.END, "Découpe commencée\n")
            self.message_text.see(tk.END)
            self.update_progress_bar(0)
            self.briot.initialize_log_file()
            self.start_button.config(text="information découpe", image=self.img_visu, compound='left', command=self.open_Visualisation)
            self.start_button.state(['!disabled'])
            self.stop_event.clear()  # Assurez-vous que l'événement d'arrêt est effacé
            self.cut_thread = threading.Thread(target=self.run_cut_process)
            self.cut_thread.daemon = True  # Définir le thread comme daemon
            self.cut_thread.start()  
        else:
            messagebox.showerror("Error Tool" , "Outils non initilaliser") 
        
    def run_cut_process(self):
        self.briot.log_clear()
        if laserReady == 0 or (laserReady == 2 and self.laserCom == None): # tu n'es pas dans les dipos laser ou windows sans com n'est pas initialiser
            for i in range(len(self.file)):
                if self.stop_event.is_set():
                    self.message_text.insert(tk.END, "Découpe arrêtée par l'utilisateur\n")
                    self.message_text.see(tk.END)
                    break
                self.briot.send_position(self.file[i])
                self.update_progress_bar((i*100)/len(self.file))

        else : # utilisation du laser 
            if (self.laserPower <= 0):
                for i in range(len(self.file)):
                    if self.stop_event.is_set():
                        self.message_text.insert(tk.END, "Découpe arrêtée par l'utilisateur\n")
                        self.message_text.see(tk.END)
                        break
                    self.briot.send_position(self.file[i])
                    self.update_progress_bar((i*100)/len(self.file))  
            elif(laserReady == 1) : # tu veux utiliser le laser rasberry
                laser = False 
                self.laserBp.state(['!disabled'])
                self.laserBp.config
                for i in range(len(self.file)):
                    if self.stop_event.is_set():
                        self.message_text.insert(tk.END, "Découpe arrêtée par l'utilisateur\n")
                        self.message_text.see(tk.END)
                        break
                    try :
                        if ((self.file[i][:2] == "@0f" ) == False  or len(self.file)<=0): # si ce nes pas un commande pour indique les sense de rotation , et que la taille est coérente 
                            if( self.file[i].split(',')[-3] != str(self.briot.speed) and laser== False):
                                laser = True
                                self.pwm.start(self.laserPower)
                            elif (self.file[i].split(',')[-3] == str(self.briot.speed) and laser == True):
                                laser = False 
                                self.pwm.stop()
                        elif(laser == False):
                            laser == True
                            self.pwm.start(self.laserPower)
                    except :
                        None
                        #print(f" {self.file[i]} \n up  {self.briot.speed} ")
                    self.briot.send_position(self.file[i])
                    self.update_progress_bar((i*100)/len(self.file)) 
                self.pwm.stop()
            else : #tu veux utiliser le laser avec un windows et la com a été initialiser 
                laser = False 
                self.laserBp.state(['!disabled'])
                self.laserBp.config
                for i in range(len(self.file)):
                    if self.stop_event.is_set():
                        self.message_text.insert(tk.END, "Découpe arrêtée par l'utilisateur\n")
                        self.message_text.see(tk.END)
                        break 
                    try :
                        if ((self.file[i][:2] == "@0f" ) == False  or len(self.file)<=0): # si ce nes pas un commande pour indique les sense de rotation , et que la taille est coérente 
                            if( self.file[i].split(',')[-3] != str(self.briot.speed) and laser== False):
                                laser = True
                                self.laserPWMsend(self.laserPower)
                            elif (self.file[i].split(',')[-3] == str(self.briot.speed) and laser == True):
                                laser = False 
                                self.laserPWMsend(0)
                        elif(laser == False):
                            laser == True
                            self.laserPWMsend(self.laserPower)
                    except :
                        None
                        #print(f" {self.file[i]} \n up  {self.briot.speed} ")
                    self.briot.send_position(self.file[i])
                    self.update_progress_bar((i*100)/len(self.file))
                self.laserPWMsend(0)

        self.stop_tool()

        self.message_text.insert(tk.END, "Découpe terminée\n")
        self.message_text.see(tk.END)
        self.start_button.config( text="Lancer la découpe", image=self.img_start, compound='left' ,command=self.start_cut)
        self.start_button.state(['disabled']) 
        self.tooltips[self.start_button].update_text("Start Cut \n")

        self.stop_button.config( text="Plateau Disponible", command=self.stop  , style="Stop.TButton")
        self.tooltips[self.stop_button].update_text("relancer")

        self.update_progress_bar(0)
         
    def stop(self):
        self.stop_event.set()  # Déclenche l'événement d'arrêt
        self.stop_tool()
        self.update_progress_bar(0)
        if (laserReady == 1)  :self.pwm.stop()
        self.message_text.insert(tk.END, "Arrêté\n")
        self.message_text.see(tk.END)
        self.start_button.config( text="Lancer la découpe", image=self.img_start, compound='left' ,command=self.start_cut)
        self.stop_button.config( text="Arrêt STOP") 
        self.tooltips[self.stop_button].update_text("Stop")
        if( self.briot.state == True):
            self.enable_buttons()
        else:
            self.disable_buttons()
            self.connect_button.config(state=tk.ACTIVE)

    def connect(self):
        if(self.briot.ser == None):
            if platform.system() == 'Linux': # autre méthode de port sur linux
                self.briot = CNC('/dev/ttyUSB0')
            else :
                self.briot = CNC() #si pas connecter réinisialiste 
            self.briot.DefSpeed(35)
        message = self.briot.initialisation_connexion()
        if (message == "Bien Connecter"):
            self.message_text.insert(tk.END, "Connexion réussie\n")
            self.message_text.see(tk.END)
            self.enable_buttons()
            if (self.briot.state == True):
                self.connect_button.config(state=tk.DISABLED)  
        else:
            self.message_text.insert(tk.END, str(message)+"\n") 
            self.message_text.see(tk.END)
            self.show_ports_window()

    def show_ports_window(self):
        self.ports_window = tk.Toplevel(self.master)
        self.ports_window.title("Ports disponibles")
        self.ports_window.geometry("300x200")

        label = tk.Label(self.ports_window, text="Sélectionnez un port :")
        label.pack(pady=10)

        self.selected_port = tk.StringVar()
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        port_menu = ttk.Combobox(self.ports_window, textvariable=self.selected_port, values=port_list)
        port_menu.pack(pady=10)

        retry_button = ttk.Button(self.ports_window, text="Réessayer la connexion", command=self.retry_connection)
        retry_button.pack(pady=10) 

    def retry_connection(self):
        selected_port = self.selected_port.get()
        if selected_port:
            self.briot = CNC(selected_port)
            message = self.briot.initialisation_connexion()
            if message == "Bien connecté":
                self.message_text.insert(tk.END, "Connexion réussie\n")
                self.message_text.see(tk.END)
                self.connect_button.config(state=tk.DISABLED)
                self.enable_buttons()
                self.ports_window.destroy()
                self.briot.DefSpeed(30)
            else:
                self.message_text.insert(tk.END, str(message) + "\n")
                self.message_text.see(tk.END)             

    def start_tool(self):
        message = self.briot.Start_Tool() 
        self.briot.Close_Door()
        if message == "0":
            self.message_text.insert(tk.END, f"Outil démarré, porte verrouillée : {message}\n")
            self.message_text.see(tk.END)
            messagebox.showwarning("Vérification de l'outil", "Vérifiez que l'outil tourne !\nIl a son propre interrupteur.")
            self.infoTool = True
        else:
            self.message_text.insert(tk.END, f"Outil non démarré : {message}\n")
            self.message_text.see(tk.END)

    def stop_tool(self):
        message = self.briot.Stop_Tool()
        self.briot.Open_Door()
        if message == "0":
            self.message_text.insert(tk.END, f"Outil arrêté, porte déverrouillée : {message}\n")
            self.message_text.see(tk.END)
            self.infoTool = False
        else:
            self.message_text.insert(tk.END, f"Erreur : {message}\n")
            self.message_text.see(tk.END)
            self.infoTool = False

        if laserReady == 1:
            self.pwm.stop()

        if laserReady == 2 :
            if self.laserCom != None: self.laserPWMsend(str(0))
       
    def laserPowerSelect(self):
        if laserReady == 0:
            self.message_text.insert(tk.END, "Laser non disponible pour votre situaution\n")
        else:
            self.infoTool = True
            # Fonction pour définir la puissance du laser à l'aide d'une barre de choix
            def set_laser_power(value):
                value = self.laserPower
                self.message_text.insert(tk.END, f"La puissance du laser a été définie à : {self.laserPower}\n")

            # Création de la fenêtre Toplevel pour la configuration du laser
            self.laserConfig = tk.Toplevel(self.master)
            self.laserConfig.title("Configuration du Laser")
            
            # Définir une taille minimale pour la fenêtre
            self.laserConfig.wm_minsize(400, 200)
            self.laserConfig.geometry("500x300")

            
            # Charger l'image pour l'arrière-plan
            background_image = self.img_power_laser

            # Étiquette pour l'arrière-plan avec l'image
            background_label = ttk.Label(self.laserConfig, image=background_image)
            background_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

            # Pour empêcher Python de supprimer l'image trop tôt, on attache une référence à l'objet.
            background_label.image = background_image

            # Label pour indiquer la puissance du laser comme un titre en grand
            label = ttk.Label(self.laserConfig, text="Puissance du Laser", font=("Helvetica", 16, "bold"), background='grey')
            label.place(relx=0.5, y=20, anchor=tk.CENTER)

            # Barre de choix (Scale) pour définir la puissance du laser
            scale = ttk.Scale(self.laserConfig, from_=-1, to=100, orient=tk.HORIZONTAL, command=set_laser_power)
            scale.place(relx=0.5, y=60, anchor=tk.CENTER, relwidth=0.95)

            # Étiquette pour afficher la valeur sélectionnée de la barre de choix
            value_label = ttk.Label(self.laserConfig, text=str(round(self.laserPower)))
            value_label.place(relx=0.5, y=100, anchor=tk.CENTER)

            # Fonction pour mettre à jour la valeur affichée lorsque la barre de choix est déplacée
            def update_value_label(value):
                if (float(value) <= 0 ):
                    value_label.config(text="Déactiver")
                    self.laserPower = -1
                else :
                    value_label.config(text=round(float(value), 1))
                    self.laserPower = round(float(value),4)

            # Lier la fonction de mise à jour à la barre de choix (Scale)
            scale.config(command=update_value_label)

            # Bouton pour fermer la fenêtre Toplevel
            close_button = ttk.Button(self.laserConfig, text="Fermer", command=self.closeConLaser)
            close_button.place(relx=0.5, rely=0.9, anchor=tk.CENTER)

           # Empêcher la redimension de la fenêtre en dessous de la taille minimale
            self.laserConfig.resizable(True, True)
            self.laserConfig.update_idletasks()  # Make sure the window is fully rendered before enforcing size constraints
            current_width = self.laserConfig.winfo_width()
            current_height = self.laserConfig.winfo_height()
            if current_width < 400 or current_height < 200:
                self.laserConfig.minsize(max(400, current_width), max(200, current_height))
        
    def closeConLaser(self): # doit appler une fonction pour marcher 
        if (self.laserPower >0):
            self.message_text.insert(tk.END, f"Puissance du Laser: {round(self.laserPower,1)}\n")
        else :
            self.message_text.insert(tk.END, "Laser non activé\n")
        self.message_text.see(tk.END)       
        self.laserConfig.destroy()
    
    def laserComOpen(self): # fenetre de sélection de ports # pour windows ou carte pilotable
        self.port_Pwm_fenaitre = tk.Toplevel(self.master)
        self.port_Pwm_fenaitre.title("Ports de connection Module PWM")
        self.port_Pwm_fenaitre.geometry("400x280")
    
        canvas = tk.Canvas(self.port_Pwm_fenaitre, width=400, height=280)
        canvas.pack(fill="both", expand=True)
    
        # Chargez et redimensionnez l'image pour qu'elle prenne tout l'espace de la fenêtre 
        original_image = self.img_laser_Select
        resized_image = original_image.resize((400, 280), Image.LANCZOS)
        self.img_laser_Select = ImageTk.PhotoImage(resized_image)
    
        # Met l'image en arrière-plan
        canvas.create_image(0, 0, image=self.img_laser_Select, anchor="nw")
    
        # Créez les widgets et placez-les au centre
        label = tk.Label(self.port_Pwm_fenaitre, text="Sélectionnez un port :")
        canvas.create_window(200, 80, window=label)
    
        self.selected_port = tk.StringVar()
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        port_menu = ttk.Combobox(self.port_Pwm_fenaitre, textvariable=self.selected_port, values=port_list)
        canvas.create_window(200, 120, window=port_menu)
    
        retry_button = ttk.Button(self.port_Pwm_fenaitre, text="Connexion Appareil", command=self.laserModuleConection)
        canvas.create_window(200, 160, window=retry_button)
        
    def laserModuleConection(self): # fonction peut se connecter
        selected_port = self.selected_port.get()
        back = ""

        def read_response():
            nonlocal back
            try:
                back = self.laserCom.readline().decode('utf-8', errors='ignore').strip()
            except:
                back = "error"

        if self.laserCom is None:  # si non initialisé alors tente connection sinon teste et supprime connection
            try:
                self.laserCom = serial.Serial(selected_port, 250000)
                ordre = "0"
                self.laserCom.write(ordre.encode('utf-8'))

                read_thread = threading.Thread(target=read_response)
                read_thread.start()
                read_thread.join(timeout=2)  # timeout de 2 secondes

                if back == "error" or back != "Null":
                    self.laserCom = None
                else:
                    self.port_Pwm_fenaitre.destroy()
                    self.laserBp.config(text='LASER', command=self.laserPowerSelect, image=self.img_laser)
                    self.message_text.insert(tk.END, "Connexion avec le module laser réussie"+"\n") 
                    self.message_text.see(tk.END)
            except:
                print('erreur module PWM')
                self.laserCom = None

        else:
            try:
                ordre = "0"
                self.laserCom.write(ordre.encode('utf-8'))

                read_thread = threading.Thread(target=read_response)
                read_thread.start()
                read_thread.join(timeout=2)  # timeout de 2 secondes

                if back == "error" or back != "Null":
                    self.laserCom = None
            except:
                try:
                    self.laserCom.close()  # tentative de libérer la communication en cas d'erreur dans la variable
                except:
                    pass
                self.laserCom = None

    def laserPWMsend(self ,puissance:float) -> bool :
        try :
            puissance = str(round(puissance,2))
        except:
            None
        if ( self.laserCom  != None) :
            self.laserCom.write((puissance + '\n').encode('utf-8'))
            back = ""

        def read_response():
            nonlocal back
            try:
                back = self.laserCom.readline().decode('utf-8', errors='ignore').strip()
            except:
                back = "error"
        try :
            read_thread = threading.Thread(target=read_response)
            read_thread.start()
            read_thread.join(timeout=2)
        except:
            back= "error"
        #print("retout esp :", back)
        if back == "error"  :
                return False
        elif  back != str('Null'):
            return True
        elif (len(back.split(' ')) >= 1 ) :
            try :
                if (back.split(' ')[2] != puissance ) : return False
            except: 
                None
            return True
        else: return True
        
    def update_progress_bar(self,value : float):
        if value < 0:
            value = 1
        elif value > 100:
            value = 100
        self.progress.set(value)

    def home_machine(self):
        message = self.briot.AutoHome()
        self.message_text.insert(tk.END, f"home: {message}\n")
        self.message_text.see(tk.END)

    def initConnection(self):
        self.briot = CNC()
        self.briot.DefSpeed(2100) # 35 mm/s en mm/min
    
    def on_closing(self):
        self.stop_event.set()  # Déclenche l'événement d'arrêt
        self.briot.deconnection()
        if laserReady == 1 :
            self.pwm.stop()
            GPIO.cleanup()
        elif (laserReady == 2):
            if self.laserCom != None: self.laserCom.close()
        self.master.destroy()

    def open_in_new_terminal(self, script_path):
        if platform.system() == 'Windows':
            subprocess.Popen(['start', 'cmd', '/c', f'python {script_path}'], shell=True)
        elif platform.system() == 'Linux':
            # Try different terminal emulators commonly available on Linux
            terminal_emulators = [
                ('gnome-terminal', ['--']),
                ('xterm', ['-e']),
                ('konsole', ['-e']),
                ('lxterminal', ['-e']),
                ('xfce4-terminal', ['--command']),
                ('mate-terminal', ['--command']),
                ('tilix', ['-e']),
                ('terminator', ['-e'])
            ]
            for terminal, option in terminal_emulators:
                if shutil.which(terminal):
                    subprocess.Popen([terminal] + option + ['python3', script_path])
                    return
            raise EnvironmentError("No supported terminal emulator found. Please install one of the following: gnome-terminal, xterm, konsole, lxterminal, xfce4-terminal, mate-terminal, tilix, terminator")
        else:
            raise NotImplementedError("Unsupported platform")
    
    def open_Visualisation(self):
        self.open_in_new_terminal('openVisu.py')
    
    def on_key_press(self, event): 
        
        if self.progress.get() != 0 or self.briot.state == False :
            None
            #print("touche = ", event.keysym)
        elif event.keysym == 'Up':
            #print("Flèche vers le haut pressée")
            self.move("Y", self.move_increment.get())
        elif event.keysym == 'Down':
            #print("Flèche vers le bas pressée")
            self.move("Y", -self.move_increment.get())
        elif event.keysym == 'Left':
            #print("Flèche vers la gauche pressée")
            self.move("X", -self.move_increment.get())
        elif event.keysym == 'Right':
            #print("Flèche vers la droite pressée")
            self.move("X", self.move_increment.get())
        elif event.keysym == 'plus':
            #print("plus")
            self.move("Z", self.move_increment.get())
        elif event.keysym == 'minus':
            #print("moins")
            self.move("Z", -self.move_increment.get())
        elif event.keysym == '0':
            #print("0 c'est home")
            self.home_machine()

if __name__ == "__main__":
    root = tk.Tk()
    #conection
    app = CNCInterface(master=root)
    root.mainloop()

# compile : nuitka --standalone --onefile --output-dir=dist --enable-plugin=tk-inter --include-data-dir=img=img --windows-icon-from-ico=img/icon.ico interfaceEtConect.py