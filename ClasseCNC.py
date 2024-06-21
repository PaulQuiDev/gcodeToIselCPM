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

        # max distence = lenght(mm)* 40
        self.max_x = 8000
        self.max_y = 7900 # modifier !!! orginal = 6000
        self.max_z = 4000

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
        minx , miny , maxx , maxy = self.max_x ,self.max_y,0,0
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
                    if (old_z != z) : # les courbe en 3D ne sont pas pris en compte 
                        arc_points = self.generate_arc_Z(old_x, old_y, old_z, x, y, z, d, j, word[0] in ('G2', 'G02'))
                        for ptRotate in arc_points: # vérification des arrondies 
                            x , y , z = ptRotate[0] , ptRotate[1] , ptRotate[2]
                            ordre.append(f"@0M {int(x*40 + self.x0)},{self.speed},{int(y*40 + self.y0)},{self.speed},{-abs(int(z*40 - self.z0))},{self.speed},{-abs(int(z*40 - self.z0))},{self.speed}\r")
                            posx = int(x*40 + self.x0)
                            posy = int(y*40 + self.y0 )   
                            if  (abs(z*40) + abs(self.z0) > self.max_z): #les axes sont dans le positif et ne dépasses pas le Volument de l'imprimente
                                print('Dépasse axe Z' , z)
                                return ['Dépasse axe Z']
                            if (posx > self.max_x or posx < 0):
                                print('hors max X')
                                return ['hors max X']
                            if (posy > self.max_y or posy < 0): 
                                print('hors max y')
                                return['hors max y']
                            if (posx > maxx): maxx = round( posx, -1)
                            if (posx < minx) : minx = round( posx, -1)

                            if (posy > maxy): maxy = round( posy, -1)
                            if (posy < miny) : miny = round( posy, -1)
                    else : 
                        #print('cercle avec isle')
                        arc = self.Arc_to_c142(old_x,old_y,x,y,d,j,speed,word[0] in ('G2', 'G02')) # la courbe est ralative pas besoint de la décaler par a port au nouveau origine
                        ordre.extend(arc)
                        # if error position
                        extremum = self.calculate_extremes(old_x*40 + self.x0 ,old_y*40 + self.y0 ,x*40+ self.x0,y*40+ self.y0,d*40,j*40) #calcule max tu doit être en courbe absolue 
                        if (extremum[0] > self.max_x ):
                            print('hors max X')
                            return ['hors max X']
                        if (extremum[1] < 0):
                            print('hors min X')
                            return ['hors min X']
                        if (extremum[2] > self.max_y ):
                            print ('hors max Y')
                            return ['hors max Y']
                        if (extremum[3] < 0):
                            print("hors min y")
                            return ['hors min Y']
                        if (extremum[0] > maxx): maxx = round( posx, -1)
                        if (extremum[1] < minx) : minx = round( posx, -1)

                        if (extremum[2] > maxy): maxy = round( posy, -1)
                        if (extremum[3] < miny) : miny = round( posy, -1)

                else :
                    print('Commande Non Pris en compte ' , i)

                posx = int(x*40 + self.x0) # variable hors plateau
                posy = int(y*40 + self.y0 )
                
                if  (abs(z*40) + abs(self.z0) > self.max_z): #les axes sont dans le positif et ne dépasses pas le Volument de l'imprimente
                    print('Dépasse axe Z' , z)
                    return ['Dépasse axe Z']
                if (posx > self.max_x):
                    print('hors max X')
                    return ['hors max X']
                if (posx < 0):
                    return ['hors min X']
                if (posy > self.max_y ): 
                    print('hors max y')
                    return['hors max y']
                if (posy < 0):
                    return['hors min y']
                if (posx > maxx): maxx = round( posx, -1)
                if (posx < minx) : minx = round( posx, -1)

                if (posy > maxy): maxy = round( posy, -1)
                if (posy < miny) : miny = round( posy, -1)
        #faire le dessin de la zone 
        if (self.z0 > 200): retract = 40 # pour 1 cm
        else : retract = 0
        if(minx != self.max_x or miny != self.max_y ):
            self.go_to_machin(self.x0,self.y0,(self.z0 - retract))
            self.go_to_machin(minx,miny,(self.z0-retract))
            self.go_to_machin(minx,maxy,(self.z0 -retract))
            self.go_to_machin(maxx,maxy,(self.z0 -retract))
            self.go_to_machin(maxx,miny,(self.z0 -retract))
            self.go_to_machin(minx,minx,(self.z0 -retract))

        return ordre

    def generate_arc_Z(self, x_start, y_start, z_start, x_end, y_end, z_end, i, j, clockwise, points_per_unit=4):
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

        arc_length = abs(end_angle - start_angle) * r
        num_points = max(int(arc_length * points_per_unit), 2)  # Ensure at least 2 points

        arc = np.linspace(start_angle, end_angle, num=num_points)
        x_arc = cx + r * np.cos(arc)
        y_arc = cy + r * np.sin(arc)
        z_arc = np.linspace(z_start, z_end, num=num_points)  # Interpolating Z values

        return list(zip(x_arc, y_arc, z_arc))

    def Arc_to_c142(self, old_x: float, old_y: float , X_end: float , Y_end : float , I : float , J : float ,speed : int ,clockwise : bool) -> list:
    
        # Calculate the center of the arc ,global coordonner 
        Xarc = old_x + I
        Yarc = old_y + J

        # Calculate the radius
        radius = np.sqrt(I**2 + J**2)
        R = radius * 40

        alpha = np.arctan2(-J, -I)  # Start angle
        betha = np.arctan2(Y_end - Yarc, X_end - Xarc)  # End angle

        inverse = False
        if alpha < 0:
            alpha += 2 * np.pi
        if betha < 0:
            betha += 2 * np.pi


        # Calculate the angle difference
        if clockwise:
            if betha > alpha:
                betha -= 2 * np.pi
        else:
            if alpha > betha:
                alpha -= 2 * np.pi

        total_angle = abs(betha - alpha)
        B = int(round(abs((4 * R * total_angle) / np.pi)))

        # Calculate start coordinates relative to the center
        X_start = int(round(R * np.cos(alpha)))
        Y_start = int(round(R * np.sin(alpha)))

        X_s = np.degrees(np.arctan2(-J, -I))
        print(X_s)
        # Determine Rx and Ry

        if(X_s>= 0 and X_s<90) : Rx , Ry = -1 , 1
        elif( X_s>= 90 ) : Rx , Ry = -1,-1
        elif(X_s < 0 and X_s > -90 ) : Rx ,Ry = 1 , 1
        elif (X_s <= 90 ) : Rx , Ry = 1 , -1 
        else :
            Rx , Ry = 1 , 1 
            print("Error Angles")

        if clockwise : Rx , Ry = -Rx , -Ry 

        # Speed and error factor (placeholders)
        V = speed  # steps/second, example value
        E = int(Rx * Ry * (X_start * (X_start - Rx) + Y_start * (Y_start - Ry) - R**2) // 2)  # error factor, example value

        c_command = []
        if clockwise:
            c_command.append("@0f0\r")
        else:
            c_command.append("@0f-1\r")

        # Construct the C-142 command
        c_command.append(f"@0y {B},{V},{E},{X_start},{Y_start},{Rx},{Ry}\r")

        return c_command

    def calculate_extremes(self, x_start, y_start, x_end, y_end, i, j):
        # Centre de l'arc
        cx = x_start + i
        cy = y_start + j

        # Rayon de l'arc
        radius = np.sqrt(i**2 + j**2)

        # Angles de départ et de fin
        start_angle = np.arctan2(y_start - cy, x_start - cx)
        end_angle = np.arctan2(y_end - cy, x_end - cx)

        # Angle de départ doit être dans [0, 2*pi]
        if start_angle < 0:
            start_angle += 2 * np.pi
        if end_angle < 0:
            end_angle += 2 * np.pi

        # Si l'arc passe par le 0 angle (modulo 2*pi)
        if end_angle < start_angle:
            end_angle += 2 * np.pi

        # Fonction pour vérifier si un angle est dans la plage de l'arc
        def is_in_arc(theta):
            while theta < 0:
                theta += 2 * np.pi
            while theta >= 2 * np.pi:
                theta -= 2 * np.pi
            return start_angle <= theta <= end_angle

        # Points candidats aux extrêmes
        candidate_angles = [start_angle, end_angle]

        # Ajouter les angles de 0, pi/2, pi, 3*pi/2 si ils sont dans la plage de l'arc
        for angle in [0, np.pi / 2, np.pi, 3 * np.pi / 2]:
            if is_in_arc(angle):
                candidate_angles.append(angle)

        # Calcul des positions des candidats
        candidates = [(cx + radius * np.cos(theta), cy + radius * np.sin(theta)) for theta in candidate_angles]

        # Récupération des extrêmes
        x_values = [pt[0] for pt in candidates]
        y_values = [pt[1] for pt in candidates]

        max_x = max(x_values)
        min_x = min(x_values)
        max_y = max(y_values)
        min_y = min(y_values)

        return [max_x, min_x, max_y, min_y]

    def initialisation_connexion(self) -> str:
        if (self.ser != None ):
            self.__order__("@07\r")
            self.__order__("@0R7\r")
            sorti = self._commander_("@07\r")
            print("Initialisation Connection: " , sorti )
            self._commander_("@0B1,1\r")
            self._commander_("@0B2,0\r")
            self._commander_("@0B3,1\r")
            self._commander_("@0B4,0\r")
            self._commander_("@0B5,0\r")
            self._commander_("@0B,64\r")
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
                if (instruction[:3] == "@0M") :
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
    
    def __order__(self, ordre : str)-> None:
        try:
            self.ser.write(ordre.encode('utf-8'))
        except serial.SerialException as e:
            print("erreu envoi:", e)


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
            if (X < 0 or X > int(self.max_x/40)):
                return ("x en dehors du plateau")
            elif (Y < 0 or Y > int(self.max_y/40)):
                return ("Y en dehors du plateau")
            elif (Z < 0 or Z > int(self.max_z/40)):
                return ("z en dehors du plateau")
            else:
                X = int(X) # aprés la comparaisont z peut devenir un flaout 
                Y = int(Y)
                Z = int(Z)
                return self.send_position(f"@0M {X*40},{self.speed},{Y*40},{self.speed},{-abs(Z*40)},{self.speed},{-abs(Z*40)},{self.speed}\r")
        else: print('machine non dispo')

    def go_to_machin(self,x:int,y:int,z:int)-> str: # problemme 
        if (self.state == True ):
            if (x < 0 or x > self.max_x):  
                return ("x en dehors du plateau")
            elif (y < 0 or y > self.max_y):
                return ("Y en dehors du plateau")
            elif (z < 0 or z > self.max_z):
                return ("z en dehors du plateau")
            else:
                x = int(x) # aprés la comparaisont z peut devenir un flaout 
                y = int(y)
                z = int(z)
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
        if ( (self.x + (X*40)) > 0 or (self.x + (X*40)) < self.max_x):
            return self.go_to_machin(int(self.x + X*40), int(self.y) , int(self.z))
        else: print("Position x invalide")
        
    def move_Y(self, Y: int) -> str:
        if (self.y + (Y * 40)) > 0 or (self.y + (Y * 40) < self.max_y):
            return self.go_to_machin( int(self.x), int(self.y + Y*40),  int(self.z))
        else: print("Position y invalide")

    def move_Z(self, Z: int) -> str:
        if (self.z + (Z * 40)) > 0 or (self.z + (Z * 40) < self.max_z):
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
                print("essay home position :",end="")
                self._commander_("@0R7")
                return("/" + retour + "/ Erreur Coordonner Hors plateau ou emergency tsop")
            elif retour == "9":
                return("/" + retour + "/ Erreur Alimentation couper")
            elif retour == "5": 
                return("/" + retour + "/ Erreur Bouton stop presser (esseyer de redemarer la machine) ou sintax error")
            elif retour == "3":
                return("/" + retour + "/ illegal number of axes")
            elif retour == "4":
                return("/" + retour + "/ axis not defind")
            elif retour == "7":
                print("/" + retour + "/ illegal parametre")
                return("/" + retour + "/ illegal parametre")
            elif retour == "H":
                return("/" + retour + "/ Panneau ouvert")
            else :
                return ("/" + retour + "/ Erreur de....")
    
if __name__ == "__main__":
    print("démo")
    briot = CNC(Port='COM8')

    briot.initialisation_connexion()

    briot.DefSpeed(35)

    briot.go_to_machin(1000,2500,200)
    briot.SetLocal0()
    print(briot.move_X(5))

    for i in range(5):
        print(briot.move_X(3))
    
    gcode = briot.Read_gcode('Holder.nc')
    ordre = briot.generate_order(gcode)
    
    for i in ordre :
        print(i)
        print(briot.send_position(i), end="\n\n")

    briot.Stop_Tool()

    briot.deconnection()