import serial
import numpy as np

class CNC:
    def __init__(self, Port='COM8') -> None:
        try :
            ser = serial.Serial(Port, 19200)
        except:
            print(" <|Problemme comunication avec Port|>" , Port)
            ser = None
        
        self.ser = ser
        self.state = False
        # ===== ===== = == = = === Posisiont globale
        self.x = 0 
        self.y = 0
        self.z = 0
        # ==== = = = = = = = = 
        self.speed = 100 # vitesse pour le G0 déplacement rapide 

        # ------------------------------------ Pausition 0 locale
        self.x0 = 0  
        self.y0 = 0
        self.z0 = 0

        self.log_file = 'cnc_logs.txt'
        self.initialize_log_file()

#Note : position minuscule = position lengage machine , Maj = position en mm 

    def Read_gcode(self, name_file: str) -> list:
        lignes_gcode = []
        try:
            with open(name_file, 'r') as fichier:
                for ligne in fichier:
                    # Supprimer les espaces et les sauts de ligne
                    ligne = ligne.strip()
                    # Ajouter la ligne à la liste
                    lignes_gcode.append(ligne)
        except FileNotFoundError:
            print("Le fichier spécifié n'existe pas.")
        return lignes_gcode

    def generate_order(self, gcode : list) -> list:
        instru = []
        for ligne in gcode:
            if ligne.find(';') == -1:
                instru.append(ligne)
        
        speed = 200
        x , y , z = 0 , 0 , 0  #initilaliser au 0 locale 
        d , j = 0, 0
        minx , miny , maxx , maxy = 8000 ,6000,0,0
        ordre = []
        for i in instru:
            word = i.split(' ')
            if len(word) > 1 and word[0][0] == 'G':  # commande de direction
                old_x ,old_y , old_z = x ,y ,z
                for truc in word:
                    if truc.startswith('X'):
                        x = float(truc[1:])
                        #print('x :' , x , " machin=" , x*40)
                    elif truc.startswith('Y'):
                        y = float(truc[1:])
                        #print('y :', y , " machin=" , y*40)
                    elif truc.startswith('Z'):
                        z = float(truc[1:])
                        #print('z :' , z, " machin=" , z*40)
                    elif truc.startswith('F'):
                        speed = int(float(truc[1:]))
                    # juste pour la rotation    
                    elif truc.startswith('I'):
                        d = float(truc[1:])
                    elif truc.startswith('J'):
                        j = float(truc[1:])
                    
                if (word[0] == 'G1' or word[0] == 'G01'): # suivent les versiont c'est G1 ou G01
                    ordre.append(f"@0M {int(x*40 + self.x0)},{speed},{int(y*40 + self.y0)},{speed},{(int(z*40 - self.z0))},{speed},{(int(z*40 - self.z0))},{speed}\r")
                    #self.afficher_instruction(f"@0M {int(x*40 + self.x0)},{speed},{int(y*40 + self.y0)},{speed},{(int(z*40 - self.z0))},{speed},{(int(z*40 - self.z0))},{speed}\r",ende='\n\n ')

                elif (word[0] == 'G0' or word[0] == 'G00') : #c'est un G0 mouvement rapide 
                    ordre.append(f"@0M {int(x*40 + self.x0)},{self.speed},{int(y*40 + self.y0)},{self.speed},{(int(z*40 - self.z0))},{self.speed},{(int(z*40 - self.z0))},{self.speed}\r")
                    #self.afficher_instruction(f"@0M {int(x*40 + self.x0)},{self.speed},{int(y*40 + self.y0)},{self.speed},{(int(z*40 - self.z0))},{self.speed},{(int(z*40 - self.z0))},{self.speed}\r",ende='\n\n')
                    
                elif (word[0] in ('G2', 'G02', 'G3', 'G03')): # boucle qui génere les arrondies 
                    arc_points = self.generate_arc(old_x, old_y, old_z, x, y, z, d, j, word[0] in ('G2', 'G02'))
                    for ptRotate in arc_points:

                        x , y , z = ptRotate[0] , ptRotate[1] , ptRotate[2]
                        ordre.append(f"@0M {int(x*40 + self.x0)},{self.speed},{int(y*40 + self.y0)},{self.speed},{-abs(int(z*40 - self.z0))},{self.speed},{-abs(int(z*40 - self.z0))},{self.speed}\r")
                        posx = int(x*40 + self.x0)
                        posy = int(y*40 + self.y0 )   
                        if  (abs(z*40) + abs(self.z0) > 4000): #les axes sont dans le positif et ne dépasses pas le Volument de l'imprimente
                            print('Dépasse axe Z' , z)
                            return ['Dépasse axe Z']
                        if (posx > 8000 or posx < 0):
                            print('hors max X')
                            return ['hors max X']
                        if (posy > 6000 or posy < 0): 
                            print('hors max y')
                            return['hors max y']
                        if (posx > maxx): maxx = round( posx, -1)
                        if (posx < minx) : minx = round( posx, -1)
        
                        if (posy > maxy): maxy = round( posy, -1)
                        if (posy < miny) : miny = round( posy, -1)
                else :
                    print('Commande Non Pris en compte ' , i)

                posx = int(x*40 + self.x0) # variable hors plateau
                posy = int(y*40 + self.y0 )
                
                if  (abs(z*40) + abs(self.z0) > 4000): #les axes sont dans le positif et ne dépasses pas le Volument de l'imprimente
                    print('Dépasse axe Z' , z)
                    return ['Dépasse axe Z']
                if (posx > 8000 or posx < 0):
                    print('hors max X')
                    return ['hors max X']
                if (posy > 6000 or posy < 0): 
                    print('hors max y')
                    return['hors max y']
                if (posx > maxx): maxx = round( posx, -1)
                if (posx < minx) : minx = round( posx, -1)

                if (posy > maxy): maxy = round( posy, -1)
                if (posy < miny) : miny = round( posy, -1)
        #faire le dessin de la zone 
        if (self.z0 > 200): retract = 10
        else : retract = 0
        if(minx != 8000 or miny != 6000 ):
            maxx = int(maxx/40)
            minx = int(minx/40)
            maxy = int(maxy/40)
            miny = int(miny/40)
            self.go_to(int(self.x0/40),int(self.y0/40 ),(int(self.z0/40)- retract))
            self.go_to(minx,miny,(int(self.z0/40)- retract))  # -5 pou eviter que la téte ne fortte 
            self.go_to(minx,maxy,(int(self.z0/40)- retract))
            self.go_to(maxx,maxy,(int(self.z0/40)- retract))
            self.go_to(maxx, miny,(int(self.z0/40)- retract))
            self.go_to(minx,miny,(int(self.z0/40)- retract))
        return ordre

    def generate_arc(self,x_start, y_start, z_start, x_end, y_end, z_end, i, j, clockwise, num_points=20):
        cx = x_start + i
        cy = y_start + j
        r = np.sqrt(i**2 + j**2)

        start_angle = np.arctan2(y_start - cy, x_start - cx)
        end_angle = np.arctan2(y_end - cy, x_end - cx)

        if clockwise:
            if end_angle > start_angle:
                end_angle -= 2 * np.pi
        else:
            if end_angle < start_angle:
                end_angle += 2 * np.pi

        arc = np.linspace(start_angle, end_angle, num=num_points)
        x_arc = cx + r * np.cos(arc)
        y_arc = cy + r * np.sin(arc)
        z_arc = np.linspace(z_start, z_end, num=num_points)  # Interpolating Z values

        return list(zip(x_arc, y_arc, z_arc))

    def initialisation_connexion(self) -> str:
        if (self.ser != None ):
            sorti = self._commander_("@07\r")
            print("Initialisation Connection: " , sorti )
            self._commander_("@0B1,1\r")
            self._commander_("@0B2,0\r")
            self._commander_("@0B3,1\r")
            self._commander_("@0B4,0\r")
            self._commander_("@0B5,0\r")
            self._commander_("@0B,64\r")
            if (sorti == "0"):
                sorti= self._commander_("@0R7\r")
                print("AutoHome :" , sorti )
                if (sorti == "0"):
                    self.state =True
                    self.x , self.y ,self.z = 0,0,0
                    return "Bien Connecter"
            else:
                self.state = False
                return "non disponible"
        else:
            return ("Non inisialisable ")

    def deconnection(self) -> None:
        try :
            self.Stop_Tool()
            self.ser.close()
            self.state = False
        except:
            print("Erreur Déconection")

    def show_instruction(self, instruction, ende="\n") -> None:
        instru = instruction.split(',')
        print("X: {:.2f} Y: {:.2f} Z: {:.2f} speed: {:.2f}".format(float(instru[0][4:])/40, float(instru[2])/40, float(instru[4])/40, float(instru[3])/40), end=ende)

    def send_position(self, instruction: str) -> str: # envoyer commede de position 
        if (self.state == True):
            try:
                self.ser.write(instruction.encode('utf-8'))
                instru = instruction.split(',')
                self.x , self.y , self.z = float(instru[0][4:]) , float(instru[2]) , abs(float(instru[4]))
                self.log_position(f"X{self.x},Y{self.y},Z{-self.z}")
                return self.Read_machine_message()
            except serial.SerialException as e:
                return ("Erreur lors de l'envoi de l'instruction sur le port série :", e)
        else : 
            return ("Non connecter ")
        
    def log_position(self, instruction: str) -> None:
        """Écrit les commandes de position dans un fichier texte."""
        try:
            with open(self.log_file, 'a+') as log:
                log.write(f"{instruction}\n")
        except IOError as e:
            print(f"Erreur lors de l'écriture dans le fichier de logs : {e}")

    def initialize_log_file(self) -> None:
        """Initialise (écrase) le fichier de logs."""
        try:
            with open(self.log_file, 'w+') as log:
                log.write("Log de commandes CNC\n")
        except IOError as e:
            print(f"Erreur lors de l'initialisation du fichier de logs : {e}")

    def _commander_(self, instruction: str) -> str: #ordre direct sans vérificateion de connection pas de possition
        try:
            self.ser.write(instruction.encode('utf-8'))
            return self.Read_machine_message()
        except serial.SerialException as e:
            return ("Erreur lors de l'envoi de l'instruction sur le port série :", e)
        
    def commande(self, instruction: str) -> str: #ordre direct avec vérificateion de connection , pas de possition
        if ( self.state == True):
            self.ser.write(instruction.encode('utf-8'))
            return self.Read_machine_message()
        else:
            return ("Erreur lors de l'envoi de l'instruction sur le port série :")
        
    def go_to(self,X:int,Y:int,Z:int) -> str:
        if (self.state == True ):
            if (X < 0 or X > 200):
                return ("x en dehors du plateau")
            elif (Y < 0 or Y > 150):
                return ("Y en dehors du plateau")
            elif (Z < 0 or Z > 100):
                return ("z en dehors du plateau")
            else:
                return self.send_position(f"@0M {X*40},{self.speed},{Y*40},{self.speed},{-abs(Z*40)},{self.speed},{-abs(Z*40)},{self.speed}\r")
        else: print('machine non dispo')

    def go_to_machin(self,x:int,y:int,z:int)-> str: # problemme 
        if (self.state == True ):
            if (x < 0 or x > 8000):
                return ("x en dehors du plateau")
            elif (y < 0 or y > 6000):
                return ("Y en dehors du plateau")
            elif (z < 0 or z > 4000):
                return ("z en dehors du plateau")
            else:
                #print(f"@0M {x},{self.speed},{y},{self.speed},{-abs(z)},{self.speed},{-abs(z)},{self.speed}\r")
                return self.send_position(f"@0M {x},{self.speed},{y},{self.speed},{-abs(z)},{self.speed},{-abs(z)},{self.speed}\r")
        else: print('machine non dispo')

    def SetLocal0(self) -> None:
        self.x0 = self.x
        self.y0 = self.y
        self.z0 = self.z

    def AutoHome(self) -> str:
        self.x = 0
        self.y = 0
        self.z = 0
        return self.commande("@0R7\r")

    def move_X(self , X: int) -> str:
        if ( (self.x + (X*40)) > 0 or (self.x + (X*40)) < 8000):
            return self.go_to_machin(int(self.x + X*40), int(self.y) , int(self.z))
        else: print("Position x invalide")
        
    def move_Y(self, Y: int) -> str:
        if (self.y + (Y * 40)) > 0 or (self.y + (Y * 40) < 6000):
            return self.go_to_machin( int(self.x), int(self.y + Y*40),  int(self.z))
        else: print("Position y invalide")

    def move_Z(self, Z: int) -> str:
        if (self.z + (Z * 40)) > 0 or (self.z + (Z * 40) < 4000):
            return self.go_to_machin( int(self.x),  int(self.y), int(self.z + Z ))
        else: print("Position Z invalide")
    
    def DefSpeed(self , SPEED : int) -> None: # maj a speed = mm/s pour les ordres de déplacement 
        if (SPEED > 0 and SPEED < 50):
            self.speed = SPEED*40
        else:
            print("Vitesse non conforme")

    def Start_Tool(self) -> str:
        return self.commande("@0B2,1\r")

    def Stop_Tool(self)-> str:
        return self.commande("@0B2,0\r")

    def Close_Door(self)-> str:
        return self.commande("@0B1,0\r") 

    def Open_Door(self)-> str:
        return self.commande("@0B1,1\r")

    def Read_machine_message(self) -> str: # retoune la commande de sortie si erreur la met entre /
            retour = self.ser.read(1).decode('utf-8')
            #print("Retour machine :", retour)
            if retour == "0" :
                return retour
            elif retour == "8" :
                #print("Machine non disponible ¯\_(ツ)_/¯")
                return("/" + retour + "/ Erreur Machine non démarer")
            elif retour == "2" :  
                return("/" + retour + "/ Erreur Coordonner Hors plateau ou emergency tsop")
            elif retour == "9":
                return("/" + retour + "/ Erreur Alimentation couper")
            elif retour == "5":
                return("/" + retour + "/ Erreur Bouton stop presser (esseyer de redemarer la machine)")
            elif retour == "3":
                return("/" + retour + "/ illegal number of axes")
            elif retour == "4":
                return("/" + retour + "/ axis not defind")
            elif retour == "7":
                return("/" + retour + "/ illegal parametre")
            else :
                return ("/" + retour + "/ Erreur de....")
    
if __name__ == "__main__":
    print("démo")
    briot = CNC(Port='COM8')

    briot.initialisation_connexion()

    briot.DefSpeed(35)

    briot.go_to(20,20,20)
    briot.SetLocal0()
    print(briot.move_X(5))

    for i in range(5):
        print(briot.move_X(3))
    
    gcode = briot.Read_gcode('Holder.nc')
    ordre = briot.generate_order(gcode)
    

    briot.Stop_Tool()

    briot.deconnection()