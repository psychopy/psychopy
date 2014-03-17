
/*
ioSync Sketch for Teensy 3.0 / 3.1

Copyright (C) 2013-2014 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. author:: Sol Simpson <sol@isolver-software.com>

- Maintains a 48 bit microsecond clock so rollover will only occur if MCU is running without reset for ~ 8.9 years.
- Handles serial requests from the host PC and sends necessary reply.
- If analog input events are enabled, handles reading analog input lines and streaming analog samples to Host PC
- If digital input events are enabled, handles reading digital input lines and sending a digital input event whenever the digital input byte value has changed.

ioSync assigns the Teensy 3 pins in a fixed usage mapping. See below for what that mapping is.

TODO:

- Allow some constants to be set by user. For example analog input related constants.

*/

// Misc. Util functions

byte bytePow(byte x, byte p)
{
  if (p == 0) return 1;
  if (p == 1) return x;

  byte tmp = bytePow(x, p/2);
  if (p%2 == 0) return tmp * tmp;
  else return x * tmp * tmp;
}

// PIN LABELS

// teensy 3 board led pin
#define LED 13

// Non USB UART RT and TX can be accessed using 'Serial1' object in Teensiduino
#define UART_RX RX1
#define UART_TX TX1

// give Teensy 3 Pin numbers for Digital Out
#define DO_0 2
#define DO_1 3
#define DO_2 4
#define DO_3 5
#define DO_4 25 // on bottom of T3
#define DO_5 26 // on bottom of T3
#define DO_6 27 // on bottom of T3
#define DO_7 28   // on bottom of T3

byte DOUT_PINS[8]={
  DO_0,DO_1,DO_2,DO_3,DO_4,DO_5,DO_6,DO_7};

// give Teensy 3 Pin numbers for Digital In
#define DI_0 6
#define DI_1 7
#define DI_2 8
#define DI_3 9
#define DI_4 29 // on bottom of T3
#define DI_5 30// on bottom of T3
#define DI_6 31 // on bottom of T3
#define DI_7 32 // on bottom of T3

byte DIN_PINS[8]={
  DI_0,DI_1,DI_2,DI_3,DI_4,DI_5,DI_6,DI_7};

// currently Teensy has 9 DINs setup, so we have one extra stand alone. 
#define DIN_8 33

// SPI related pins
#define SPI_SS CS0 // pin 10 on T3, Device Select
#define SPI_MOSI DOUT //pin 11 on T3, SPI Data Output 
#define SPI_MISO DIN //pin 12 on T3, SPI Data Input
#define SPI_SCK SCK // pin 13 on 3, Clock

// give Teensy 3 Pin numbers for Analog In
#define AI_0 14
#define AI_1 15
#define AI_2 16
#define AI_3 17
#define AI_4 A10 // on bottom of T3
#define AI_5 A11 // on bottom of T3
#define AI_6 A12 // on bottom of T3
#define AI_7 A13 // on bottom of T3
byte AIN_PINS[8]={
  AI_0,AI_1,AI_2,AI_3,AI_4,AI_5,AI_6,AI_7};


const double AREF_INTERVAL_V = 1.2;
const double DIGITAL_ANALOG_16_STEP = 0.00001831054687;
const double DIGITAL_ANALOG_14_STEP = 0.0000732421875;
const double DIGITAL_ANALOG_12_STEP = 0.00029296875;
const double DIGITAL_ANALOG_10_STEP = 0.001171875;

#define AIN_RES 16
#define AIN_AVERAGING 16
#define AIN_REF INTERNAL //EXTERNAL
#define AIN_RATE 1000

// I2C pins
#define I2C_SCL SCL
#define I2C_SDA SDA

// PWM pins
#define PMW_0 20
#define PMW_1 21
#define PMW_2 22
#define PMW_3 23
const byte PMW_PINS[4]={
  PMW_0,PMW_1,PMW_2,PMW_3};


//-------------------------------------------------
// 48 bit usec timer used for time stamping

struct Usec{
  unsigned long usecs;
  unsigned int rolls;
  unsigned long prev_usecs;
  byte bytes[6];
};

Usec t3_usec_time;

void updateUsecTime(){
  // Update 48 bit usec timer
  t3_usec_time.usecs=micros();
  if(t3_usec_time.usecs<t3_usec_time.prev_usecs) // its rolled over
    t3_usec_time.rolls++; // increment 2 byte roll counter
  t3_usec_time.prev_usecs=t3_usec_time.usecs; 
}

void updateUsecTimeBytes(){
  t3_usec_time.bytes[0] = ( (t3_usec_time.usecs) >> 24) & 0xff; //event time bits 24..31
  t3_usec_time.bytes[1] = ( (t3_usec_time.usecs) >> 16) & 0xff; //event time bits 16..23
  t3_usec_time.bytes[2] = ( (t3_usec_time.usecs) >> 8) & 0xff; //event time bits 8..15
  t3_usec_time.bytes[3] = ( (t3_usec_time.usecs) & 0xff);    //event time bits 0..7  
  t3_usec_time.bytes[4] = ( (t3_usec_time.rolls) >> 8) & 0xff; //roll counter bits 40..47
  t3_usec_time.bytes[5] = ( (t3_usec_time.rolls) & 0xff);    //roll counter bits 32..39
}

//----------------------------------------------------
// Data Buffer for holding bytes to be sent via
// Serial USB to Host PC

#define TX_BYTE_BUF_SIZE 88

unsigned int tx_byte_buffer_index=0;
byte tx_byte_buffer[TX_BYTE_BUF_SIZE];

unsigned int byteBufferFreeSize(){
  return TX_BYTE_BUF_SIZE-tx_byte_buffer_index;
}

byte writeByteBufferToSerial(){
  byte bsent=Serial.write((byte*)tx_byte_buffer, tx_byte_buffer_index);
  tx_byte_buffer_index=0;
  return bsent;  
}

//------------------------------------
//
// Host PC Request Functionality

#define NULL_REQUEST 0
#define GET_USEC_TIME 1
#define SET_DIGITAL_OUT_PIN 2
#define SET_DIGITAL_OUT_STATE 3
#define GET_DIGITAL_IN_STATE 4
#define GET_AIN_CHANNELS 5
#define SET_T3_INPUTS_STREAMING_STATE 6

#define REQUEST_TYPE_COUNT 7

#define REQUEST_TX_HEADER_BYTE_COUNT 8

byte request_tx_byte_length[REQUEST_TYPE_COUNT]={
  0,
  REQUEST_TX_HEADER_BYTE_COUNT,
  REQUEST_TX_HEADER_BYTE_COUNT,
  REQUEST_TX_HEADER_BYTE_COUNT+2,
  REQUEST_TX_HEADER_BYTE_COUNT+1,
  REQUEST_TX_HEADER_BYTE_COUNT+sizeof(AIN_PINS)*2,
  REQUEST_TX_HEADER_BYTE_COUNT,
};

void NullHandlerRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleUsecTimeRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleSetDigitalOutPinRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleSetDigitalOutStateRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleGetDigitalInStateRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleGetAnalogInChannelsRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleEnableInputStreamingRx(byte request_type,byte request_id,byte request_rx_byte_count);

void (*requestHandlerFP[REQUEST_TYPE_COUNT])(byte request_type,byte request_id,byte request_rx_byte_count)={
  NullHandlerRx,
  handleUsecTimeRx,
  handleSetDigitalOutPinRx,
  handleSetDigitalOutStateRx,
  handleGetDigitalInStateRx,
  handleGetAnalogInChannelsRx,
  handleEnableInputStreamingRx
};

//---------------------------------------
// Host PC Request Processor, sets Request Tx reply
// header bytes and calls necesssary
// Host PC Request Handlers.

unsigned int handleHostSerialRequests(){
  char rx_info[3];
  byte rtype,rid,rx_count;

  if (Serial.available() >=3) {  
    Serial.readBytes(rx_info,3);
    rtype=rx_info[0];
    rid=rx_info[1];
    rx_count=rx_info[2];

    updateUsecTime();
    updateUsecTimeBytes();

    tx_byte_buffer[tx_byte_buffer_index]=rid;
    tx_byte_buffer[tx_byte_buffer_index+1]=request_tx_byte_length[rtype];
    tx_byte_buffer[tx_byte_buffer_index+2]=t3_usec_time.bytes[0];
    tx_byte_buffer[tx_byte_buffer_index+3]=t3_usec_time.bytes[1];
    tx_byte_buffer[tx_byte_buffer_index+4]=t3_usec_time.bytes[2];
    tx_byte_buffer[tx_byte_buffer_index+5]=t3_usec_time.bytes[3];
    tx_byte_buffer[tx_byte_buffer_index+6]=t3_usec_time.bytes[4];
    tx_byte_buffer[tx_byte_buffer_index+7]=t3_usec_time.bytes[5];

    tx_byte_buffer_index=tx_byte_buffer_index+8;

    requestHandlerFP[rtype](rtype,rid,rx_count-8);
  }  
  return 0;  
}

//---------------------------------------
// Host PC Request Handlers
// for different Request types

void NullHandlerRx(byte request_type,byte request_id,byte request_rx_byte_count){
  //nothing to do here
}

void handleUsecTimeRx(byte request_type,byte request_id,byte request_rx_byte_count){
  //nothing to do here
}

void handleSetDigitalOutStateRx(byte request_type,byte request_id,byte request_rx_byte_count){
  /*
  SET_DIGITAL_OUT_STATE: Sets all 8 digital out pins using the bit pattern provided of the digital output lines.
   
   RX bytes ( 4 ):
   0: SET_DIGITAL_OUT_STATE
   1: Request ID
   2: Rx Byte Count
   3: 8 dout pins state (as 1 byte, 0 - 256)
   
   TX Bytes ( 7 ):
   0: Request ID
   1: Tx Byte Count
   2 - 7: usec time that pin was set.    
   */

  byte new_dout_state=Serial.read();

  int i=0;
  for (byte mask = 00000001; mask>0; mask <<= 1) { //iterate through bit mask
    digitalWrite(DOUT_PINS[i],new_dout_state & mask); // set 1
    i++;
  }
}

void handleSetDigitalOutPinRx(byte request_type,byte request_id,byte request_rx_byte_count){
  /*
  SET_DIGITAL_OUT_PIN: Sets one of the digital output lines.
   
   RX bytes ( 5 ):
   0: SET_DIGITAL_OUT_PIN
   1: Request ID
   2: Rx Byte Count
   3: pin number (0-7)
   4: pin state (0 == LOW, 1==HIGH)
   
   
   TX Bytes ( 7 ):
   0: Request ID
   1: Tx Byte Count
   2 - 7: usec time that pin was set.    
   */
  char pin_value[2]={
    0,0  }; // pin number, Pin state
  Serial.readBytes(pin_value,2);

  //  if (pin_value[1]==0)
  //    digitalWrite(DOUT_PINS[pin_value[0]],LOW); // set 0
  //  else
  //    digitalWrite(DOUT_PINS[pin_value[0]],HIGH); // set 1
  digitalWrite(DOUT_PINS[pin_value[0]],pin_value[1]);
}

void handleGetDigitalInStateRx(byte request_type,byte request_id,byte request_rx_byte_count){
  /*
  GET_DIGITAL_IN_STATE: Gets all 8 digital in pins.
   
   RX bytes ( 3 ):
   0: GET_DIGITAL_IN_STATE
   1: request ID
   2: Rx Byte Count
   
   TX Bytes ( 9 ):
   0: GET_DIGITAL_IN_STATE
   1: size of response in bytes    
   2 - 7: usec time that pin was set.
   8: digital input line value as a byte between 0 and 255    
   */
  byte din_value=0;
  for (int i=0;i<sizeof(DIN_PINS);i++)
    din_value+=bytePow(2,i)*digitalRead(DIN_PINS[i]);

  tx_byte_buffer[tx_byte_buffer_index]=din_value;
  tx_byte_buffer_index+=1; 
}

void handleGetAnalogInChannelsRx(byte request_type,byte request_id,byte request_rx_byte_count){
  /*
  GET_AIN_CHANNELS: Gets 1 - 8 values from the analog inputs
  
  RX bytes ( 3 ):
   0: GET_DIGITAL_IN_STATE
   1: request ID
   2: Rx Byte Count
   
   TX Bytes ( 25 ):
   0: Request ID
   1: Tx Byte Count
   2 - 7: usec time that pin was set.    
   8 - 24: 8 * 16 bit analog input values
   */
  unsigned int v=0;
  for (int i=0;i<sizeof(AIN_PINS);i++){
    v=analogRead(AIN_PINS[i]);
    tx_byte_buffer[tx_byte_buffer_index+8+i*2] = (v >> 8) & 0xff; //event time bits 8..15
    tx_byte_buffer[tx_byte_buffer_index+9+i*2] = (v & 0xff);    //event time bits 0..7  
    }
  tx_byte_buffer_index+=16; 
}

byte digital_input_streaming_enabled=0;
byte analog_input_streaming_enabled=0;

void handleEnableInputStreamingRx(byte request_type,byte request_id,byte request_rx_byte_count){
  char inputStreaming[2]={
    0,0  };
  Serial.readBytes(inputStreaming,2);
  digital_input_streaming_enabled=inputStreaming[0];
  analog_input_streaming_enabled=inputStreaming[1];
}

//---------------------------------------
//
// IntervalTimer for reading digital and analog inputs
#define INPUT_LINES_READ_RATE 500

byte  last_digital_input_state=0;
byte current_digital_input_state=0;

void inputLineReadTimerCallback(void){
  if (digital_input_streaming_enabled>0){
    // Check for digital input state changes
    current_digital_input_state=0;
    for (byte i=0;i<sizeof(DIN_PINS);i++)
      current_digital_input_state+=(bytePow(2,i)*digitalRead(DIN_PINS[i]));
    if (current_digital_input_state!=last_digital_input_state)
      addDigitalEventToByteBuffer(); // create digital input change event
  }

  if (analog_input_streaming_enabled>0){
    // Add Analog Input Event
    addAnalogEventToByteBuffer();
  }
}

//----------------------------------------------------
// T3 Generated Events

#define DIGITAL_INPUT_EVENT 1
#define ANALOG_INPUT_EVENT 2

#define EVENT_TX_HEADER_COUNT 8
#define DIGITAL_EVENT_TX_BYTE_COUNT 9
#define ANALOG_EVENT_TX_BYTE_COUNT 24

byte addDigitalEventToByteBuffer(){
  updateUsecTime();
  updateUsecTimeBytes();

  if (byteBufferFreeSize()<DIGITAL_EVENT_TX_BYTE_COUNT)
    return 0;

  tx_byte_buffer[tx_byte_buffer_index]=DIGITAL_INPUT_EVENT;
  tx_byte_buffer[tx_byte_buffer_index+1]=DIGITAL_EVENT_TX_BYTE_COUNT;
  tx_byte_buffer[tx_byte_buffer_index+2]=t3_usec_time.bytes[0];
  tx_byte_buffer[tx_byte_buffer_index+3]=t3_usec_time.bytes[1];
  tx_byte_buffer[tx_byte_buffer_index+4]=t3_usec_time.bytes[2];
  tx_byte_buffer[tx_byte_buffer_index+5]=t3_usec_time.bytes[3];
  tx_byte_buffer[tx_byte_buffer_index+6]=t3_usec_time.bytes[4];
  tx_byte_buffer[tx_byte_buffer_index+7]=t3_usec_time.bytes[5];
  tx_byte_buffer[tx_byte_buffer_index+8]=current_digital_input_state;
  last_digital_input_state=current_digital_input_state;       
  tx_byte_buffer_index=tx_byte_buffer_index+DIGITAL_EVENT_TX_BYTE_COUNT;

}

byte addAnalogEventToByteBuffer(){
  if (byteBufferFreeSize()<ANALOG_EVENT_TX_BYTE_COUNT)
    return 0;

  unsigned int ain_readings[sizeof(AIN_PINS)];
  for (int i=0;i<sizeof(AIN_PINS);i++)
    ain_readings[i]=analogRead(AIN_PINS[i]);

  updateUsecTime();
  updateUsecTimeBytes();

  tx_byte_buffer[tx_byte_buffer_index]=ANALOG_INPUT_EVENT;
  tx_byte_buffer[tx_byte_buffer_index+1]=ANALOG_EVENT_TX_BYTE_COUNT;
  tx_byte_buffer[tx_byte_buffer_index+2]=t3_usec_time.bytes[0];
  tx_byte_buffer[tx_byte_buffer_index+3]=t3_usec_time.bytes[1];
  tx_byte_buffer[tx_byte_buffer_index+4]=t3_usec_time.bytes[2];
  tx_byte_buffer[tx_byte_buffer_index+5]=t3_usec_time.bytes[3];
  tx_byte_buffer[tx_byte_buffer_index+6]=t3_usec_time.bytes[4];
  tx_byte_buffer[tx_byte_buffer_index+7]=t3_usec_time.bytes[5];

  tx_byte_buffer_index=tx_byte_buffer_index+8;

  for (int i=0;i<sizeof(AIN_PINS);i++){
    tx_byte_buffer[tx_byte_buffer_index+(i*2)] = (byte)(ain_readings[i] >> 8) & 0xff; //event bits 8..15
    tx_byte_buffer[tx_byte_buffer_index+1+(i*2)] = (byte)(ain_readings[i] & 0xff);    //event bits 0..7  
  }

  tx_byte_buffer_index=tx_byte_buffer_index+sizeof(AIN_PINS)*2;
}

//----------------------------------
// Initializers for various areas of functionality.

void initDigitalOutputs(){
  for (int i=0;i<sizeof(DOUT_PINS);i++){
    pinMode(DOUT_PINS[i], OUTPUT);
    digitalWrite(DOUT_PINS[i], LOW);
  }  
}
 
void initDigitalInputs(){
  for (int i=0;i<sizeof(DIN_PINS);i++){
    pinMode(DIN_PINS[i], INPUT);
  }
}

void initAnalogInputs(){
  for (int i=0;i<sizeof(AIN_PINS);i++){
    pinMode(AIN_PINS[i], INPUT);
  }
  // Analog input bit resolution 10 - 16 bits are supported
  analogReadRes(AIN_RES);

  // HW Analog Input Sample Averaging. 1 = No Averaging to 32 = average 32 samples in HW, max value is 32
  analogReadAveraging(AIN_AVERAGING);

  // What should be used as the analog reference source.
  // Options: 
  //  DEFAULT: ??
  //  INTERNAL:  1.0 ±0.3V (0.97 to 1.03 V) (source http://www.pjrc.com/teensy/K20P64M50SF0.pdf)
  //  EXTERNAL: Use the input applied to the AGND. See here from some considerations if this is used. http://forum.pjrc.com/threads/23585-AREF-is-making-me-lose-my-hair 
  analogReference(AIN_REF);
}

void initUsec48(){
  t3_usec_time.prev_usecs=micros();
  t3_usec_time.usecs=t3_usec_time.prev_usecs;
  t3_usec_time.rolls=0;
}

//----------------------------------
// Teensy 3 Init, called each time the microcontroller is reset or powered on.

void setup()
{
  Serial.begin(115200);
  initUsec48();
  initDigitalOutputs();
  initDigitalInputs();
  initAnalogInputs();
  //  initIntervalTimers();
}

//---------------------------------------
// Main loop()
// Repeatedly called while microcontroller is running.
#define MAX_TX_BUFFERING_INTERVAL 700

elapsedMicros sinceLastSerialTx;
elapsedMicros sinceLastInputRead;
void loop()
{
  handleHostSerialRequests();

  if (sinceLastInputRead>=INPUT_LINES_READ_RATE){
    inputLineReadTimerCallback();   
    sinceLastInputRead=sinceLastInputRead-INPUT_LINES_READ_RATE;
  }

  if ( tx_byte_buffer_index>0 && (byteBufferFreeSize()<24 || sinceLastSerialTx>=MAX_TX_BUFFERING_INTERVAL) ){
    writeByteBufferToSerial();
    Serial.flush();
    Serial.send_now();
    sinceLastSerialTx = sinceLastSerialTx - MAX_TX_BUFFERING_INTERVAL;
  }
}

