// Sweep
// by BARRAGAN <http://barraganstudio.com> 
// This example code is in the public domain.


#include <Servo.h> 
 
Servo myservo2;  // create servo object to control a servo 
                // a maximum of eight servo objects can be created 
Servo myservo3;
int pos = 0;    // variable to store the servo position 
 
void setup() 
{ 
  myservo2.attach(5);  // attaches the servo on pin 9 to the servo object 
  myservo3.attach(9);
} 
 
 
void loop() 
{ 
  for(pos = 120; pos > 40; pos -= 1)  // goes from 0 degrees to 180 degrees 
  {                                  // in steps of 1 degree 
    myservo3.write(pos);              // tell servo to go to position in variable 'pos' 
    delay(15);                       // waits 15ms for the servo to reach the position 
  } 
  delay(500);
  
  for(pos = 40; pos <80; pos+=1)
  {
    myservo2.write(pos);
    delay(15);
  }
  delay(500);
  
  for(pos = 80; pos>40; pos-=1)
  {
    myservo2.write(pos);
    delay(15);
  }
  delay(500);
  
  for(pos = 40; pos<120; pos+=1)     // goes from 180 degrees to 0 degrees 
  {                                
    myservo3.write(pos);              // tell servo to go to position in variable 'pos' 
    delay(15);                       // waits 15ms for the servo to reach the position 
  } 
} 
