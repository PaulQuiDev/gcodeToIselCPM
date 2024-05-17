import serial

class CNC:
    def __init__(self, Port='COM8') -> None:
        try :
            ser = serial.Serial(Port, 19200)
        except:
            print(" <|Problemme comunication avec Port|>" , Port)
            ser = None
        
        self.ser = ser
        self.eta = False
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


#Note : position minuscule = position lengage machine , Maj = position en mm 

    def lire_fichier_gcode(self, nom_fichier: str) -> list:
        lignes_gcode = []
        try:
            with open(nom_fichier, 'r') as fichier:
                for ligne in fichier:
                    # Supprimer les espaces et les sauts de ligne
                    ligne = ligne.strip()
                    # Ajouter la ligne à la liste
                    lignes_gcode.append(ligne)
        except FileNotFoundError:
            print("Le fichier spécifié n'existe pas.")
        return lignes_gcode

    def generer_ordres(self, gcode : list) -> list:
        instru = []
        for ligne in gcode:
            if ligne.find(';') == -1:
                instru.append(ligne)
        
        speed = 200
        x , y , z = 0 , 0 , 0  #initilaliser au 0 locale 
        minx , miny , maxx , maxy = 8000 ,6000,0,0
        ordre = []
        for i in instru:
            a = i.split(' ')
            if len(a) > 1 and a[0][0] == 'G':  # commande de direction
                for truc in a:
                    if truc.find('X') != -1:
                        x = float(truc.removeprefix('X'))
                        #print('x :' , x , " machin=" , x*40)
                    if truc.find('Y') != -1:
                        y = float(truc.removeprefix('Y'))
                        #print('y :', y , " machin=" , y*40)
                    if truc.find('Z') != -1:
                        z = float(truc.removeprefix('Z'))
                        #print('z :' , z, " machin=" , z*40)
                    if truc.find('F') != -1:
                        speed = int(float(truc.removeprefix('F')))
                if (i[1] == '1' or i[2] == '1'): # suivent les versiont c'est G1 ou G01
                    ordre.append(f"@0M {int(x*40 + self.x0)},{speed},{int(y*40 + self.y0)},{speed},{(int(z*40 - self.z0))},{speed},{(int(z*40 - self.z0))},{speed}\r")
                    #self.afficher_instruction(f"@0M {int(x*40 + self.x0)},{speed},{int(y*40 + self.y0)},{speed},{(int(z*40 - self.z0))},{speed},{(int(z*40 - self.z0))},{speed}\r",ende='\n\n ')

                elif (i[1] == '0' or i[2] == '0') : #c'est un G0 mouvement rapide 
                    ordre.append(f"@0M {int(x*40 + self.x0)},{self.speed},{int(y*40 + self.y0)},{self.speed},{(int(z*40 - self.z0))},{self.speed},{(int(z*40 - self.z0))},{self.speed}\r")
                    #self.afficher_instruction(f"@0M {int(x*40 + self.x0)},{self.speed},{int(y*40 + self.y0)},{self.speed},{(int(z*40 - self.z0))},{self.speed},{(int(z*40 - self.z0))},{self.speed}\r",ende='\n\n')
                else :
                    print('Commande Non Pris en compte ' , i)
                posx = int(x*40 + self.x0)
                posy = int(y*40 + self.y0 )

                if  (abs(z*40) + abs(self.z0) > 4000): #les axes sont dans le positif et ne dépasses pas le Volument de l'imprimente
                    print('Dépasse axe Z' , z)
                    return []
                if (posx > 8000 or posx < 0):
                    print('hors max X')
                    return []
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
            self.allezA(int(self.x0/40),int(self.y0/40 ),(int(self.z0/40)- retract))
            self.allezA(minx,miny,(int(self.z0/40)- retract))  # -5 pou eviter que la téte ne fortte 
            self.allezA(minx,maxy,(int(self.z0/40)- retract))
            self.allezA(maxx,maxy,(int(self.z0/40)- retract))
            self.allezA(maxx, miny,(int(self.z0/40)- retract))
            self.allezA(minx,miny,(int(self.z0/40)- retract))
        return ordre

    def initialisation_connexion(self) -> None:
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
                    self.eta =True
                    self.x , self.y ,self.z = 0,0,0
                
            else:
                self.eta = False
        else:
            print("Non inisialisable ")

    def deconnection(self) -> None:
        try :
            self.OutilsStop()
            self.ser.close()
            self.eta = False
        except:
            print("Erreur Déconection")

    def afficher_instruction(self, instruction, ende="\n") -> None:
        instru = instruction.split(',')
        print("X: {:.2f} Y: {:.2f} Z: {:.2f} speed: {:.2f}".format(float(instru[0][4:])/40, float(instru[2])/40, float(instru[4])/40, float(instru[3])/40), end=ende)

    def envoyer_Posistion(self, instruction: str) -> str: # envoyer commede de position 
        if (self.eta == True):
            try:
                self.ser.write(instruction.encode('utf-8'))
                instru = instruction.split(',')
                self.x , self.y , self.z = float(instru[0][4:]) , float(instru[2]) , abs(float(instru[4]))
                return self.lire_retour_machine()
            except serial.SerialException as e:
                return ("Erreur lors de l'envoi de l'instruction sur le port série :", e)
        else : 
            return ("Non connecter ")
        
    def _commander_(self, instruction: str) -> str: #ordre direct sans vérificateion de connection pas de possition
        try:
            self.ser.write(instruction.encode('utf-8'))
            return self.lire_retour_machine()
        except serial.SerialException as e:
            return ("Erreur lors de l'envoi de l'instruction sur le port série :", e)
        
    def commande(self, instruction: str) -> str: #ordre direct sans vérificateion de connection pas de possition
        if ( self.eta == True):
            self.ser.write(instruction.encode('utf-8'))
            return self.lire_retour_machine()
        else:
            return ("Erreur lors de l'envoi de l'instruction sur le port série :")
        
    def allezA(self,X:int,Y:int,Z:int) -> str:
        if (self.eta == True ):
            if (X < 0 or X > 200):
                return ("x en dehors du plateau")
            elif (Y < 0 or Y > 150):
                return ("Y en dehors du plateau")
            elif (Z < 0 or Z > 100):
                return ("z en dehors du plateau")
            else:
                return self.envoyer_Posistion(f"@0M {X*40},{self.speed},{Y*40},{self.speed},{-abs(Z*40)},{self.speed},{-abs(Z*40)},{self.speed}\r")
        else: print('machine non dispo')

    def allezAMachine(self,x:int,y:int,z:int)-> str: # problemme 
        if (self.eta == True ):
            if (x < 0 or x > 8000):
                return ("x en dehors du plateau")
            elif (y < 0 or y > 6000):
                return ("Y en dehors du plateau")
            elif (z < 0 or z > 4000):
                return ("z en dehors du plateau")
            else:
                print(f"@0M {x},{self.speed},{y},{self.speed},{-abs(z)},{self.speed},{-abs(z)},{self.speed}\r")
                return self.envoyer_Posistion(f"@0M {x},{self.speed},{y},{self.speed},{-abs(z)},{self.speed},{-abs(z)},{self.speed}\r")
        else: print('machine non dispo')

    def SetLocal0(self) -> None:
        self.x0 = self.x
        self.y0 = self.y
        self.z0 = self.z

    def AutoHome(self) -> str:
        return self.commande("@0R7\r")

    def DeplacerX(self , X: int) -> str:
        if ( (self.x + (X*40)) < 0 or (self.x + (X*40)) > (200*40)):
            return self.allezAMachine((self.x + X*40), self.y , self.z)
        else: print("Position x invalide")
        
    def DeplacerY(self, Y: int) -> str:
        if (self.y + (Y * 40)) < 0 or (self.y + (Y * 40)) > (150 * 40):
            return self.allezAMachine(self.x, (self.y + Y), self.z)
        else: print("Position y invalide")

    def DeplacerZ(self, Z: int) -> str:
        if (self.z + (Z * 40)) < 0 or (self.z + (Z * 40)) > (100 * 40):
            return self.allezAMachine(self.x, self.y, (self.z + Z ))
        else: print("Position Z invalide")
    
    def DefVitess(self , SPEED : int) -> None: # maj a speed = mm/s pour les ordres de déplacement 
        if (SPEED > 0 and SPEED < 50):
            self.speed = SPEED*40
        else:
            print("Vitesse non conforme")

    def OutilsDemarer(self) -> str:
        return self.commande("@0B2,1\r")

    def OutilsStop(self)-> str:
        return self.commande("@0B2,0\r")

    def PorteBloquer(self)-> str:
        return self.commande("@0B1,0\r")

    def PorteOuvrire(self)-> str:
        return self.commande("@0B1,1\r")

    def lire_retour_machine(self) -> str: # retoune la commande de sortie si erreur la met entre /
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
                return("/" + retour + "/ Erreur Bouton stop presser")
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

    briot.DefVitess(20)

    briot.allezA(140,29,31)
    briot.SetLocal0()

    gcode = briot.lire_fichier_gcode("Holder.nc")
    instruction = briot.generer_ordres(gcode)
    
    
    briot.OutilsDemarer()

    for i in instruction:
        briot.afficher_instruction(i, ende="\t")
        print(briot.envoyer_Posistion(i))


    briot.OutilsStop()

    briot.deconnection()