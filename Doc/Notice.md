# Notice d'utilisation de l'application de contrôle CNC Isel par G-code

## Introduction
Bienvenue dans la notice d'utilisation de l'application de contrôle CNC. Cette application vous permet de contrôler votre machine CNC de manière intuitive et efficace.

## Table des matières
1. [Installation](#installation)
2. [Guide d'utilisation](#utilisation-du-programme)
3. [Fonctionnalités principales](#fonctionnalités)
4. [Dépannage](#dépannage)
5. [FAQ](#faq)

## Installation
### Prérequis
- Système d'exploitation : Windows 10, macOS 10.14 ou supérieur, Linux Ubuntu 18.04 ou supérieur.
- Minimum 4 Go de RAM.
- Python 3.11 ou un environnement virtuel (si vous n'utilisez pas le fichier exécutable).
- Raspberry Pi 4 ou plus.
- Une méthode de connexion entre votre ordinateur et la machine Isel.

### Étapes d'installation
#### Depuis la release
1. Téléchargez la dernière version de l'application sur GitHub [lien de téléchargement](https://github.com/PaulQuiDev/gcodeToIselCPM/releases).
2. Exécutez le fichier gcodeToIselCPM en fonction de votre système d'exploitation (le fichier doit être déplacé avec sa dépendance _internal).
   - Sinon, suivez les instructions d'installation Depuis git.

#### Depuis Git
1. Clonez le projet dans une invite de commande :
   ```sh 
   git clone https://github.com/PaulQuiDev/gcodeToIselCPM
    ```
2. Ouvrez le répertoire du projet dans une invite de commande et exécutez :
    ```sh 
    pip install .
    ```

### Utilisation du Programme
1. Une fois le câble branché entre votre ordinateur et la machine, cliquez sur le bouton `Connection`. 
![imgCon](https://github.com/user-attachments/assets/08870c1a-47ab-4114-81ee-398ec36bc379)<br>
Si la connexion automatique échoue, une fenêtre s'ouvrira. Vous pourrez alors sélectionner le bon port et cliquer sur Réessayer la connexion dans cette fenêtre.
<p style="text-align: center;">
  <img src="https://github.com/user-attachments/assets/961bddfa-f19c-4db5-9af2-c28090a8a5cf" alt="Sélectione le port et clique sur Réessayer" width="140">
</p>
<a id='etape2'> </a>

2.  Définissez l'origine des déplacements de votre fichier à l'aide des 4 niveaux de vitesse. 
<p style="text-align: center;">
  <img src="https://github.com/user-attachments/assets/511acf54-e9ed-4af4-a142-6b378e158407" alt="Cliquer dans le cercle pour séléctionne la bonne vitesse" width="300">
 </p>

Utilisez les flèches pour déplacer la tête. La vitesse Z a été réduite pour ralentir la descente et éviter de casser une tête. Lorsque votre tête est bien placée, appuyez sur le bouton `Définir Point 0`.
<p style="text-align: center;">
<img src="https://github.com/user-attachments/assets/247f00b9-30c8-43e1-91a5-b3c78adc0035" alt="Cliquer dans le cercle pour séléctionne la bonne vitesse" width="180"> </p>

3. Chargez votre fichier (G-code, NC, ...) à l'aide du bouton Charger.
<p style="text-align: center;">
<img src="https://github.com/user-attachments/assets/5b97af96-0377-406a-8e48-a2cdfd61a2c5" alt="Cliquer dans le cercle pour séléctionne la bonne vitesse" width="110"> </p>

4. Fermez la fenêtre d'affichage de votre fichier.
<p style="text-align: left;">
  <img src="https://github.com/user-attachments/assets/b8f4147c-0bb0-4479-a42a-a2f27f410de7" alt="Cliquer dans le cercle pour séléctionne la bonne vitesse" width="130" style="float: right; margin-left: 10px;">
  La machine dessine alors un carré qui correspond au point maximal du fichier. Vérifiez que celui-ci soit bien cohérent par rapport à votre pièce. Si vous voulez changer le point d'origine, vous devez recommencer à partir de l'étape <a href="#etape2">2</a>. Déplacez la tête, appuyez sur <code>Définir point 0</code> et réouvrez votre fichier.
  </p>
<br>
 

5. Sélectionnez votre outil, appuyez sur le bouton `Activer tool`. Attention, cela ferme l'ouverture de la porte de votre machine. Vous devez cliquer sur `Stop tool` pour pouvoir la rouvrir.
 <p style="text-align: center;">
  <img src="https://github.com/user-attachments/assets/e9e68284-7933-4fee-9ca7-5eb44e79a20c" alt="Cliquer dans le cercle pour séléctionne la bonne vitesse" width="150" >
  </p>

<p style="text-align: right;">
  <img src="https://github.com/user-attachments/assets/e27adbb9-0b20-47bd-aa82-67af3e1effcb" alt="Cliquer dans le cercle pour séléctionne la bonne vitesse" width="75" style="float: left; margin-right: 10px;">

Pour utiliser l'option découpe laser, vous devez être sur un <b>Raspberry Pi sous Linux</b>. Dans ce cas, un bouton apparaît pour définir la puissance du laser <code>Puissance laser</code>. Sélectionnez une puissance non nulle et la machine effectuera une découpe laser. <br> <br> </p>

6. Lancez la découpe grâce au bouton Lancer la découpe.
<p style="text-align: left;">
  <img src="https://github.com/user-attachments/assets/d8021c71-cafc-43a4-8eb8-7d32af664a3f" alt="Cliquer dans le cercle pour séléctionne la bonne vitesse" width="190" style="float: right; margin-left: 10px;">
   Vous devez rester à côté de votre machine. En cas d'urgence, appuyez toujours sur le bouton d'urgence de la machine. Vous pouvez voir l'avancement de la découpe grâce au bouton <code>Visualisation</code>. </p>

7. Pour relancer une nouvelle découpe, cliquez sur Plateau disponible. À ce moment, l'origine reste inchangée par rapport à votre dernière configuration.

## Fonctionnalités
### Interface utilisateur
- **Connection** : Essaie de se connecter au port par défaut, sinon ouvre une fenêtre pour choisir le port de connexion.
- **Flaiche de contrôle** :Permet de déplacer les axes de la CNC. Les déplacements sur l'axe Z (hauteur) sont plus lents pour éviter les mauvaises manipulations.
- **Home** :  Lance un auto-home, les trois axes se positionnent à leur point 0.
- **Chargement de fichiers** : Importez des fichiers G-code et prévisualisez les déplacements. Si vous changez l'origine de la pièce, vous devrez recharger votre fichier.
- **Stop** : Met fin à l'exécution du code en cours.
- **Plateau disponible** :  Permet de déverrouiller les commandes.
- **Visualisation** : Ouvre une nouvelle fenêtre pour afficher les points parcourus.
- **Puissance laser** :  Si vous êtes sur un Raspberry Pi sous Linux, permet de configurer la machine pour la découpe laser et préciser la puissance du laser. Si elle est mise à 0, le laser est désactivé.
- **Deff origine** : Permet de définir le point d'origine de votre fichier. S'il est pressé alors que la position des trois axes est à 0, il charge celui utilisé pour la dernière découpe.

### Surveillance et sécurité
- **Arrêt d'urgence** : Bouton pour arrêter immédiatement la machine en cas de problème.
- **Surveillance en temps réel** : Affiche les coordonnées actuelles et l'état des axes.

## Dépannage
### Problèmes courants
- **La CNC ne se connecte pas** : Vérifiez le câble USB et assurez-vous que le bon port est sélectionné.
- **La machine ne bouge pas** : Vérifiez qu'un axe n'est pas bloqué en coupant le courant et en le déplaçant à la main.
- **La machine ne veut pas se connecter** : La machine peut avoir des soucis de connexion lorsqu'elle oublie la position des axes. Faites un auto-home, puis réessayez la connexion.



## FAQ
**Q : Puis-je utiliser des fichiers G-code créés avec un autre logiciel ?**<br>
R : Oui, l'application supporte les fichiers G-code standards. Les tests de fonctionnement ont été réalisés avec le logiciel Estlcam V11. Je vous conseille de l'utiliser si le vôtre ne donne pas l'effet escompté.

**Q : Comment mettre à jour l'application ?**<br>
R : Si vous avez téléchargé l'application sous forme d'exécutable, supprimez le dossier et retéléchargez-le. Sinon, ouvrez le dossier et dans une invite de commande tapez :
```sh
git pull
```
**Q : Peut-on utiliser le même point d'origine plusieurs fois ?**<br>
R : On ne peut réutiliser que le point d'origine de la dernière découpe. Pour cela, appuyez sur le bouton Home puis sur le bouton Origine.

**Q : Pendant une découpe, peut-on changer la vitesse ?**<br>
R : Non, la vitesse reste constante. Si vous voulez la changer, vous devez générer un autre G-code.

**Q : Peut-on définir manuellement un point d'origine ?**<br>
R : Oui, vous pouvez. Pour cela, ouvrez le fichier log_cnc.txt et modifiez les valeurs de X, Y, Z à la première ligne par celles souhaitées. Attention, l'unité est le millimètre multiplié par 40.

**Q : Les courbes vont trop loin !!**<br>
R : Il y a un problème d'approximation dans la génération des courbes lié aux commandes G02/G03. La documentation manque pour cette machine... Vous pouvez changer cela dans la classe CNC en choisissant d'appeler la méthode courbeZ. Cependant, cette méthode ne permet pas le contrôle de la vitesse.

Merci d'utiliser notre application de contrôle de machine Isel par G-code !