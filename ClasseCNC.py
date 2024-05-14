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
        self.x = 0  
        self.y = 0
        self.z = 0
        self.speed = 100

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

        speed = 500
        x , y , z = 0 , 0 , 0  #initilaliser a 0
        ordre = []
        for i in instru:
            a = i.split(' ')
            if len(a) > 2 and a[0][0] == 'G':  # commande de direction
                for truc in a:
                    if truc.find('X') != -1:
                        x = int(float(truc.removeprefix('X')))
                    if truc.find('Y') != -1:
                        y = int(float(truc.removeprefix('Y')))
                    if truc.find('Z') != -1:
                        z = int(float(truc.removeprefix('Z')))
                ordre.append('@0M ' + str(x*40) + "," + str(speed) + "," + str(y*40) + "," + str(speed) + "," + str(z*(-40)) + "," + str(speed) + "," + str(z*(-40)) +  "," + str(speed) + "\r")
        return ordre

    def initialisation_connexion(self) -> None:
        if (self.ser != None ):
            sorti = self._commander_("@07\r")
            print("Initialisation Connection: " , sorti )
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
        print("X: {:.2f} Y: {:.2f} Z: {:.2f} speed: {:.2f}".format(float(instru[0][4:])/40, float(instru[2])/40, abs(float(instru[4]))/40, float(instru[2])/40), end=ende)

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
        if (self.eta != True ):
            if (X < 0 or X > 200):
                return ("x en dehors du plateau")
            elif (Y < 0 or Y > 150):
                return ("Y en dehors du plateau")
            elif (Z < 0 or Z > 100):
                return ("z en dehors du plateau")
            else:
                self.envoyer_Posistion('@0M ' + str(X*40) + "," + str(self.speed) + "," + str(Y*40) + "," + str(self.speed) + "," + str(Z*(-40)) + "," + str(self.speed) + "," + str(Z*(-40)) +  "," + str(self.speed) + "\r")
    
    def allezAMachine(self,x:int,y:int,z:int)-> str:
        if (self.eta != True ):
            if (x < 0 or x > 8000):
                return ("x en dehors du plateau")
            elif (y < 0 or y > 6000):
                return ("Y en dehors du plateau")
            elif (z < 0 or z > 4000):
                return ("z en dehors du plateau")
            else:
                self.envoyer_Posistion('@0M ' + str(x) + "," + str(self.speed) + "," + str(y) + "," + str(self.speed) + "," + str(z*(-1)) + "," + str(self.speed) + "," + str(z*(-1)) +  "," + str(self.speed) + "\r")


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
                return("/" + retour + "/ Erreur Coordonner Hors plateau")
            elif retour == "9":
                return("/" + retour + "/ Erreur Alimentation couper")
            elif retour == "5":
                return("/" + retour + "/ Erreur Bouton stop presser")
            elif retour == "2":
                return( retour + " Probleme Ordre non compris")
            else :
                return ("/" + retour + "/ Erreur de....")
    
if __name__ == "__main__":
    print("démo")
    briot = CNC(Port='COM8')

    briot.initialisation_connexion()

    briot.DefVitess(20)

    briot.allezA(15,25,10)

    briot.AutoHome()

    gcode = briot.lire_fichier_gcode("logo(2).gcode")
    ordre = briot.generer_ordres(gcode)

    briot.OutilsDemarer()

    for i in ordre:
        briot.afficher_instruction(i,ende = "\t")
        print(briot.envoyer_Posistion(i))
    
    briot.OutilsStop()

    briot.deconnection()