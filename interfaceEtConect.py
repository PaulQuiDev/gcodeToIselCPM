import tkinter as tk
from tkinter import ttk, filedialog , messagebox
from PIL import Image, ImageTk
from ClasseCNC import CNC
import threading    

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

class CNCInterface:
    def __init__(self, master):
        self.master = master
        self.master.title("CNC Interface")
        self.master.configure(bg='grey')

        self.move_increment = tk.IntVar(value=1)  # Variable pour l'incrément de déplacement
        self.progress = tk.DoubleVar()

        self.stop_event = threading.Event()  # Variable de contrôle pour arrêter le processus

        self.file = None
        self.load_images()
        self.create_widgets()
        self.setup_grid()
        self.initConection()

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        style = ttk.Style()
        style.configure("TButton", background="grey", borderwidth=1, relief="flat")

        # Frame pour les boutons de direction
        self.direction_frame = ttk.LabelFrame(self.master, padding="10 10 10 10",text='Controle Machine')
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

        self.increment_100mm_button = ttk.Radiobutton(self.increment_frame, text="100 mm", variable=self.move_increment, value=100)
        self.increment_10mm_button = ttk.Radiobutton(self.increment_frame, text="10 mm", variable=self.move_increment, value=10)
        self.increment_5mm_button = ttk.Radiobutton(self.increment_frame, text="5 mm", variable=self.move_increment, value=5)
        self.increment_1mm_button = ttk.Radiobutton(self.increment_frame, text="1 mm", variable=self.move_increment, value=1)

        self.increment_100mm_button.grid(row=0, column=0, sticky="nsew")
        self.increment_10mm_button.grid(row=0, column=1, sticky="nsew")
        self.increment_5mm_button.grid(row=0, column=2, sticky="nsew")
        self.increment_1mm_button.grid(row=0, column=3, sticky="nsew")

        # Bouton pour définir le point 0
        self.define_button = ttk.Button(self.master, text="Définir Point 0",compound='right', image=self.img_Pt0 ,command=self.define_point)
        self.define_button.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Boutons pour charger le fichier et lancer la découpe
        self.load_button = ttk.Button(self.master, text='Load Fichier', image=self.img_open, command=self.load_file)
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
        self.stop_button = ttk.Button(self.master, text="Arrêt STOP", command=self.stop, style="Stop.TButton")
        self.stop_button.grid(row=5, column=0, padx=10, pady=10, sticky="nsew")

        self.connect_button = ttk.Button(self.master, text="Connexion", command=self.connect)
        self.connect_button.grid(row=5, column=1, padx=10, pady=10, sticky="nsew")

        # Tooltips
        Tooltip(self.x_minus_button, "-X")
        Tooltip(self.x_plus_button, "+X")
        Tooltip(self.y_minus_button, "-Y")
        Tooltip(self.y_plus_button, "+Y")
        Tooltip(self.z_minus_button, "-Z")
        Tooltip(self.z_plus_button, "+Z")
        Tooltip(self.load_button, " charger un fichier ")
        Tooltip(self.start_button, " Vérifier tout avent de lancer")
        Tooltip(self.start_tool_button, "Démarre l'outil")
        Tooltip(self.stop_tool_button, "Arrête l'outil")
        Tooltip(self.home_button, "Home")


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
        # Charger les images pour les boutons de direction
        self.img_open = ImageTk.PhotoImage(Image.open("img/open.png").resize((150, 150)))
        self.img_start = ImageTk.PhotoImage(Image.open("img/start.png").resize((90, 50)))
        self.img_mouvY = ImageTk.PhotoImage(Image.open("img/mouv.png").resize((50, 50)))
        self.img_mouvy = ImageTk.PhotoImage(Image.open("img/mouv.png").resize((50, 50)).rotate(180))
        self.img_mouvx = ImageTk.PhotoImage(Image.open("img/mouv.png").resize((50, 50)).rotate(90))
        self.img_mouvX = ImageTk.PhotoImage(Image.open("img/mouv.png").resize((50, 50)).rotate(270))
        self.img_mouvZ = ImageTk.PhotoImage(Image.open("img/mouvZ.png").resize((80, 80)))
        self.img_mouvz = ImageTk.PhotoImage(Image.open("img/mouvZ.png").resize((80, 80)).rotate(180))
        self.img_toolStart = ImageTk.PhotoImage(Image.open("img/outilS.png").resize((40, 40)))
        self.img_toolStop = ImageTk.PhotoImage(Image.open("img/outilO.png").resize((40, 40)))
        self.img_home = ImageTk.PhotoImage(Image.open("img/home.png").resize((50,50)))
        self.img_Pt0 = ImageTk.PhotoImage(Image.open("img/spot0.png").resize((50,50)))

    def move(self,  axis : str , amount: int):
        message = ""
        if(axis == "X"):
            message = self.briot.move_X(amount)
        elif( axis == "Y"):
            message = self.briot.move_Y(amount)
        elif(axis == "Z"):
            message = self.briot.move_Z(amount)
        else:
            message= "Move don't understood"

        self.message_text.insert(tk.END, f"Move {axis} by {amount} statu : {message}\n")
        self.message_text.see(tk.END)

    def define_point(self):
        self.briot.SetLocal0()
        self.message_text.insert(tk.END, f"Point 0 défini at X:{self.briot.x} Y:{self.briot.y} Z:{self.briot.z} \n")
        self.message_text.see(tk.END)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("GCode files", "*.*",)])
        try :
            self.file = self.briot.Read_gcode(file_path) # ne pas faire conficne a l'utilisateur 
        except:
            self.message_text.insert(tk.END, "Erreur Format fichier\n")
            self.message_text.see(tk.END)
        if isinstance(self.file,list) :
            self.message_text.insert(tk.END, f"Fichier chargé: {file_path}\n")
            self.message_text.see(tk.END)
            
            try :
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
        if (isinstance(self.infoTool,bool)):
            self.message_text.insert(tk.END, "Découpe commencée\n")
            self.message_text.see(tk.END)
            self.update_progress_bar(0)
            
            self.stop_event.clear()  # Assurez-vous que l'événement d'arrêt est effacé

            self.cut_thread = threading.Thread(target=self.run_cut_process)
            self.cut_thread.daemon = True  # Définir le thread comme daemon
            self.cut_thread.start()  
        else:
            messagebox.showerror("Error Tool" , "Outils non initilaliser")
        
    def run_cut_process(self):
        for i in range(len(self.file)):
            if self.stop_event.is_set():
                self.message_text.insert(tk.END, "Découpe arrêtée par l'utilisateur\n")
                self.message_text.see(tk.END)
                break
            self.briot.send_position(self.file[i])
            self.update_progress_bar((i*100)/len(self.file))
            

        self.message_text.insert(tk.END, "Découpe terminée\n")
        self.message_text.see(tk.END)

    def stop(self):
        self.stop_event.set()  # Déclenche l'événement d'arrêt
        self.stop_tool()
        self.message_text.insert(tk.END, "Arrêté\n")
        self.message_text.see(tk.END)

    def connect(self):
        if(self.briot.ser == None):
            self.briot = CNC() #si pas connecter réinisialiste 
            self.briot.DefSpeed(35)
        message = self.briot.initialisation_connexion()
        if (message == "Bien Connecter"):
            self.message_text.insert(tk.END, "Connexion réussie\n")
            self.message_text.see(tk.END)
            if (self.briot.state == True):
                self.connect_button.config(state=tk.DISABLED)
        else:
            self.message_text.insert(tk.END, str(message)+"\n")
            self.message_text.see(tk.END)

    def start_tool(self):
        message = self.briot.Start_Tool()
        self.briot.Close_Door()
        if (message == "0"):
            self.message_text.insert(tk.END, f"Outil démarré porte verrouillée {message}\n")
            self.message_text.see(tk.END)
            messagebox.showwarning("Vérif outils" , "Vérifier que l'outils tourne !\nIl a sont propre intérupteur")
            self.infoTool = True
        else:
            self.message_text.insert(tk.END, f"Outil non demarrer {message}\n")
            self.message_text.see(tk.END)

    def stop_tool(self):
        message = self.briot.Stop_Tool()
        self.briot.Open_Door()
        if (message == "0"):
            self.message_text.insert(tk.END, f"Outil arrêté Porte deverrouillée {message}\n")
            self.message_text.see(tk.END)
            self.infoTool= False
        else:
            self.message_text.insert(tk.END, f"erreur {message}\n")
            self.message_text.see(tk.END)
            self.infoTool= False
            
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

    def initConection(self):
        self.briot = CNC()
        self.briot.DefSpeed(35)
    
    def on_closing(self):
        self.stop_event.set()  # Déclenche l'événement d'arrêt
        self.briot.deconnection()
        self.master.destroy()

    
if __name__ == "__main__":
    root = tk.Tk()
    app = CNCInterface(master=root)
    root.mainloop()