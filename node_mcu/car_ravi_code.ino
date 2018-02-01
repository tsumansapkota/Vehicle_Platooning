#include "ESP8266WiFi.h"

#define rf D7
#define rb D8
#define re 3 //RX

#define lf D0
#define lb D1
#define le D2

#define leftEncoder D3
#define rightEncoder 9

const char*  ssid = "Ravi";
const char* pass = "ravigiri1818v";

String data = "";
int temp0=5, temp1=5, temp2=0, temp3=0;
int read0=0, read1=0;
float tempf=0.0f;
long templ = 0L;

WiFiClient client;
WiFiServer server(9819);

void checkClient();
void connect();

void setup()
{
    Serial.begin(115200);
    pinMode(re, OUTPUT);
    digitalWrite(re, HIGH);
    pinMode(le, OUTPUT);
    digitalWrite(le, HIGH);

    pinMode(leftEncoder, INPUT);
    digitalWrite(leftEncoder, LOW);

    pinMode(rightEncoder, INPUT);
    digitalWrite(rightEncoder, LOW);
  
    int numberOfNetworks = WiFi.scanNetworks();
   
    for(int i =0; i<numberOfNetworks; i++){
   
        Serial.print("Network name: ");
        Serial.println(WiFi.SSID(i));
        Serial.print("Signal strength: ");
        Serial.println(WiFi.RSSI(i));
        Serial.println("-----------------------");
   
    }
    connect();
    server.begin();
}

void connect()
{
    WiFi.disconnect();
    WiFi.begin(ssid, pass);
    while (WiFi.status() != WL_CONNECTED )
    {
        delay(500);
    }
    Serial.println(WiFi.localIP());
}

void checkClient()
{
  if (client)
  {
    while (client.connected())
    {
      bool avail = false;
      while (client.available() > 0)
      {
        data = client.readStringUntil('\n');
        Serial.println(data);
        for(int i=0; i< data.length(); i++){
          int chars = data.charAt(i);
          switch(chars){
            case 30://left wheel
              i++;
              chars = data.charAt(i)-20;
              leftWheel(chars*10.23);
              Serial.print("left wheel = ");
              Serial.println(chars*10.23);
              break;
            case 31: //right wheel
              i++;
              chars = data.charAt(i)-20;
              rightWheel(chars*10.23);
              Serial.print("right wheel = ");
              Serial.println(chars*10.23);
              break;
            case 32://left wheel
              i++;
              chars = data.charAt(i)-20;
              leftWheel(-chars*10.23);
              Serial.print("left wheel = ");
              Serial.println(-chars*10.23);
              break;
            case 33: //right wheel
              i++;
              chars = data.charAt(i)-20;
              rightWheel(-chars*10.23);
              Serial.print("right wheel = ");
              Serial.println(-chars*10.23);
              break;
          }
          Serial.println(chars);
        }
        client.println("rcv="+data);
      }
      data = "";
      read0 = digitalRead(leftEncoder);
      read1 = digitalRead(rightEncoder);
      if (read0 != temp0){
        temp0 = read0;
        data = data+ "le="+read0 +"\n";
        digitalWrite(leftEncoder, !read0);
      }
      if (read1 != temp1){
        temp1 = read1;
        data = data+ "re="+read1 +"\n";
        digitalWrite(rightEncoder, !read1);
      }
      if (data.length()>0)
        client.println(data);
      
    }
    client.stop();
    Serial.println("Client Disconnected");
  }
}

void rightWheel(int speeds)
{
    if (speeds > 1){
      analogWrite(rf, speeds);
      analogWrite(rb, 0);
    }
    else if (speeds < -1){
      analogWrite(rf, 0);
      analogWrite(rb, -speeds);  
    }
    else{
      analogWrite(rf, 0);
      analogWrite(rb, 0);
    }
}

void leftWheel(int speeds)
{
    if (speeds > 1){
      analogWrite(lf, speeds);
      analogWrite(lb, 0);
    }
    else if (speeds < -1){
      analogWrite(lf, 0);
      analogWrite(lb, -speeds);  
    }
    else{
      analogWrite(lf, 0);
      analogWrite(lb, 0);
    }
}

void stopCar()
{
    analogWrite(lf, 0);
    analogWrite(lb, 0);
    analogWrite(rf, 0);
    analogWrite(rb, 0);
}

void loop()
{
    client = server.available();
    checkClient();
}
