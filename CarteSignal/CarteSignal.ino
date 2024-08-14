const int pwmPin = 2;  // GPIO2 pour le signal PWM 

void setup() {
  // Initialiser la communication série à 250000 bauds
  Serial.begin(250000);
  
  // Initialiser le port D4 comme une sortie pour le PWM
  pinMode(pwmPin, OUTPUT);
  
  // Afficher un message initial pour indiquer que l'ESP8266 est prêt 
  Serial.println("ESP8266 est prêt. Envoyez un pourcentage de 0 à 100.");
}

void loop() {
  // Vérifier si des données sont disponibles sur le port série
  if (Serial.available() > 0) {
    // Lire la valeur reçue en pourcentage
    String received = Serial.readStringUntil('\n');
    float percentage = received.toFloat();  // Convertir la chaîne reçue en flottant
    
    // Limiter le pourcentage entre 0 et 100
    if (percentage < 0.0) percentage = 0.0;
    if (percentage > 100.0) percentage = 100.0;

    analogWriteFreq(30000); 
    // Calculer la valeur de cycle de travail pour le PWM (de 0 à 1023)
    float dutyCycle = map(percentage, 0.0, 100.0, 0.0, 1023.0);
    
    // Ajuster le signal PWM sur le port D4
    analogWrite(pwmPin, (int)dutyCycle);
    
    if (percentage == 0.0)
    {
      Serial.println("Null");
    }
    else
    {
      // Afficher le pourcentage et le cycle de travail dans le moniteur série
      Serial.print("Reçu : ");
      Serial.println(percentage);
    }
    
  }
}
