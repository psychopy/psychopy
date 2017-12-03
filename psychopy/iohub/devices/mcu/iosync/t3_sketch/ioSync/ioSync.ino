/*
ioSync Sketch for Teensy 3.0 / 3.1 / 3.2

Copyright (C) 2013-2016 iSolver Software Solutions
Distributed under the terms of the GNU General Public License
(GPL version 3 or any later version).

.. author:: Sol Simpson <sol@isolver-software.com>
*/

#define EXT_LED 24

// ****** Program control defines *******
//
// Change based on desired usage of ioSync

// >>>>>> KEYBOARD DEVICE <<<<<<<
//
// GENERATE_KEYBOARD_EVENT support:
//   To enable:
//     - Uncomment the below KEYBOARD define.
//     - Ensure Tools -> USB Type is set to "Serial + Keyboard + ....".
//     - Rebuild the iosync sketch and upload it.
//
//   To disable:
//     - Comment out the below KEYBOARD define.
//     - Ensure Tools -> USB Type is set to "Serial" only.
//     - Rebuild the iosync sketch and upload it.
//
#define KEYBOARD

// >>>>>> DIGITAL_INPUT_TYPE <<<<<<<
//
// Setting Digital Input Type ( INPUT or INPUT_PULLUP )
// or, if using modified Teensiduino code as of March 31, 2016
// INPUT_PULLDOWN is also supported.
#define DIGITAL_INPUT_TYPE INPUT_PULLUP

// >>>>>> LED Pin To Use <<<<<<<
//
// If ioSync is in an enclosure that has a status LED mounted to
// the enclosure panel, use EXT_LED for STATUS_LED.
// If using ioSync with Teensy on a breadboard, just use pin 13, the onboard LED for status
//
//#define STATUS_LED EXT_LED
#define STATUS_LED 13

// ****** END Program control define code section. *******

// Teensy 3 version check
#ifdef __MK20DX128__
#define TEENSY_3
#endif

#ifdef __MK20DX256__
#define TEENSY_3_1
#endif

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

byte DOUT_PINS[8]={DO_0,DO_1,DO_2,DO_3,DO_4,DO_5,DO_6,DO_7};

// give Teensy 3 Pin numbers for Digital In
#define DI_0 6
#define DI_1 7
#define DI_2 8
#define DI_3 9
#define DI_4 29 // on bottom of T3
#define DI_5 30// on bottom of T3
#define DI_6 31 // on bottom of T3
#define DI_7 32 // on bottom of T3

byte DIN_PINS[8]={DI_0,DI_1,DI_2,DI_3,DI_4,DI_5,DI_6,DI_7};

// SPI related pins
#define SPI_SS CS0 // pin 10 on T3, Device Select
#define SPI_MOSI DOUT //pin 11 on T3, SPI Data Output
#define SPI_MISO DIN //pin 12 on T3, SPI Data Input
#define SPI_SCK SCK // pin 13 on 3, Clock

#ifdef TEENSY_3_1
// Set A14 to be used as DAC channel
#define AO_0 A14
#endif


// give Teensy 3 Pin numbers for Analog In
#define AI_0 14
#define AI_1 15
#define AI_2 16
#define AI_3 17
#define AI_4 A10 // on bottom of T3
#define AI_5 A11 // on bottom of T3
#define AI_6 A12 // on bottom of T3
#define AI_7 A13 // on bottom of T3
byte AIN_PINS[8]={ AI_0,AI_1,AI_2,AI_3,AI_4,AI_5,AI_6,AI_7};

// AIN_THRESHOLD_LEVELS are set by the user, specifying
// the AIN value at which a THRESHOLD_EVENT should be triggered.
// A THRESHOLD_EVENT is triggered each time the analog input for a
// AIN line goes above , or falls, below, the threshold
unsigned int AIN_THRESHOLD_LEVELS[8]={0,0,0,0,0,0,0,0};

// Stores the threshold state for each AIN line.
// 0 == below threshold, 1 == above threshold.
// When the threshold state changes for an analog input line,
// a threshold event is created.
byte AIN_THRESHOLD_STATES[8]={0,0,0,0,0,0,0,0};

const double AREF_INTERVAL_V = 1.2;
const double DIGITAL_ANALOG_16_STEP = 0.00001831054687;
const double DIGITAL_ANALOG_14_STEP = 0.0000732421875;
const double DIGITAL_ANALOG_12_STEP = 0.00029296875;
const double DIGITAL_ANALOG_10_STEP = 0.001171875;

#define AIN_RES 16
#define AIN_AVERAGING 8
//  AIN_REF Options:
//  DEFAULT: 0.0 - +3.3 V
//  INTERNAL: 1.0 ±0.3V (0.97 to 1.03 V)
//            (source http://www.pjrc.com/teensy/K20P64M50SF0.pdf)
//  EXTERNAL: Use the input applied to the AREF / AGND.
//            See http://forum.pjrc.com/threads/23585-AREF-is-making-me-lose-my-hair
//            fom some considerations if this is used.
#define AIN_REF DEFAULT
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
// SW RESET

#define RESTART_ADDR       0xE000ED0C
#define READ_RESTART()     (*(volatile uint32_t *)RESTART_ADDR)
#define WRITE_RESTART(val) ((*(volatile uint32_t *)RESTART_ADDR) = (val))

void SW_RESTART(){
    // 0000101111110100000000000000100
    // Assert [2]SYSRESETREQ
    WRITE_RESTART(0x5FA0004);
}

// reboot CPU, call CPU_RESTART within the app. -------------
#define CPU_RESTART_ADDR (uint32_t *)0xE000ED0C
#define CPU_RESTART_VAL 0x5FA0004
#define CPU_RESTART (*CPU_RESTART_ADDR = CPU_RESTART_VAL);

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

    // update byte stream rep of current time
    //event time bits 24..31
    t3_usec_time.bytes[0] = ( (t3_usec_time.usecs) >> 24) & 0xff;
     //event time bits 16..23
    t3_usec_time.bytes[1] = ( (t3_usec_time.usecs) >> 16) & 0xff;
    //event time bits 8..15
    t3_usec_time.bytes[2] = ( (t3_usec_time.usecs) >> 8) & 0xff;
    //event time bits 0..7
    t3_usec_time.bytes[3] = ( (t3_usec_time.usecs) & 0xff);
    //roll counter bits 40..47
    t3_usec_time.bytes[4] = ( (t3_usec_time.rolls) >> 8) & 0xff;
    //roll counter bits 32..39
    t3_usec_time.bytes[5] = ( (t3_usec_time.rolls) & 0xff);
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
#define SYNC_TIME_BASE 7
#define RESET_STATE 8
#define GENERATE_KEYBOARD_EVENT 9
#define SET_ANALOG_THRESHOLDS 10
#define SET_ANALOG_OUTPUT 11
#define REQUEST_TYPE_COUNT 12

#define REQUEST_TX_HEADER_BYTE_COUNT 8

byte request_tx_byte_length[REQUEST_TYPE_COUNT]={
    0,
    REQUEST_TX_HEADER_BYTE_COUNT,
    REQUEST_TX_HEADER_BYTE_COUNT,
    REQUEST_TX_HEADER_BYTE_COUNT+2,
    REQUEST_TX_HEADER_BYTE_COUNT+1,
    REQUEST_TX_HEADER_BYTE_COUNT+sizeof(AIN_PINS)*2,
    REQUEST_TX_HEADER_BYTE_COUNT,
    REQUEST_TX_HEADER_BYTE_COUNT,
    REQUEST_TX_HEADER_BYTE_COUNT,
    REQUEST_TX_HEADER_BYTE_COUNT+5,
    REQUEST_TX_HEADER_BYTE_COUNT,
    REQUEST_TX_HEADER_BYTE_COUNT+2
};

void NullHandlerRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleUsecTimeRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleSetDigitalOutPinRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleSetDigitalOutStateRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleGetDigitalInStateRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleGetAnalogInChannelsRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleEnableInputStreamingRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleSyncTimebaseRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleResetStateRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleGenerateKeyboardEventRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleSetAnalogThresholdsEventRx(byte request_type,byte request_id,byte request_rx_byte_count);
void handleSetAnalogOutRx(byte request_type,byte request_id,byte request_rx_byte_count);

void (*requestHandlerFP[REQUEST_TYPE_COUNT])(byte request_type,byte request_id,byte request_rx_byte_count)={
    NullHandlerRx,
    handleUsecTimeRx,
    handleSetDigitalOutPinRx,
    handleSetDigitalOutStateRx,
    handleGetDigitalInStateRx,
    handleGetAnalogInChannelsRx,
    handleEnableInputStreamingRx,
    handleSyncTimebaseRx,
    handleResetStateRx,
    handleGenerateKeyboardEventRx,
    handleSetAnalogThresholdsEventRx,
    handleSetAnalogOutRx
};

elapsedMicros sinceLastSerialTx;
elapsedMicros sinceLastInputRead;
#define MAX_TX_BUFFERING_INTERVAL 700

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
    ;
}

//------------------------

void handleUsecTimeRx(byte request_type,byte request_id,byte request_rx_byte_count){
    //nothing to do here
    ;
}

//------------------------

void handleSyncTimebaseRx(byte request_type,byte request_id,byte request_rx_byte_count){
    //force immediate tx of response.
    sinceLastSerialTx = sinceLastSerialTx + MAX_TX_BUFFERING_INTERVAL;
}

//------------------------

void handleSetDigitalOutStateRx(byte request_type,byte request_id,byte request_rx_byte_count){
    /*
    SET_DIGITAL_OUT_STATE: Sets all 8 digital out pins using the bit pattern
    provided of the digital output lines.

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
    byte dout=Serial.read();
    ((dout & 0x01)) ? digitalWriteFast(2, HIGH) : digitalWriteFast(2, LOW);
    ((dout & 0x02)) ? digitalWriteFast(3, HIGH) : digitalWriteFast(3, LOW);
    ((dout & 0x04)) ? digitalWriteFast(4, HIGH) : digitalWriteFast(4, LOW);
    ((dout & 0x08)) ? digitalWriteFast(5, HIGH) : digitalWriteFast(5, LOW);
    ((dout & 0x10)) ? digitalWriteFast(25, HIGH) : digitalWriteFast(25, LOW);
    ((dout & 0x20)) ? digitalWriteFast(26, HIGH) : digitalWriteFast(26, LOW);
    ((dout & 0x40)) ? digitalWriteFast(27, HIGH) : digitalWriteFast(27, LOW);
    ((dout & 0x80)) ? digitalWriteFast(28, HIGH) : digitalWriteFast(28, LOW);
}

//------------------------
void handleSetAnalogOutRx(byte request_type,byte request_id,byte request_rx_byte_count){
    /*
    SET_ANALOG_OUTPUT: Sets the analog output line (AO_0; a.k.a A14)
    to the 12 bit value given as part of the input.

    RX bytes ( 4 ):
    0: SET_ANALOG_OUTPUT
    1: Request ID
    2: Rx Byte Count
    3-4: 12 bit output value packed in two bytes

    TX Bytes ( 7 ):
    0: Request ID
    1: Tx Byte Count
    2 - 7: usec time that pin was set.
    */
    char dac_value[2]={
    0,0  }; //12 bit output value packed in two bytes
    Serial.readBytes(dac_value,2);

    #ifdef TEENSY_3_1

    // TODO : COMPLETE !!!
    // Python Side needs to be completed too!
    #endif

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
    char pin_value[2]={0,0}; // pin number, Pin state
    Serial.readBytes(pin_value,2);
    digitalWriteFast(DOUT_PINS[(byte)pin_value[0]],(byte)pin_value[1]);
}

//------------------------
#ifdef KEYBOARD
elapsedMillis since_key1_press;
unsigned int key1_msec_dur=0;

void handleGenerateKeyboardEventRx(byte request_type,byte request_id,byte request_rx_byte_count){
    /*
    GENERATE_KEYBOARD_EVENT: Generates a USB keyboard event on the Host PC.

    RX bytes ( 5 ):
    0: SET_DIGITAL_OUT_PIN
    1: Request ID
    2: Rx Byte Count
    3-4: unsigned short for keyboard symbol constant
         in arduino\hardware\teensy\avr\cores\teensy3\keylayouts.h
    5-6: unsigned short for keyboard mofifier constants (OR'ed)
         in arduino\hardware\teensy\avr\cores\teensy3\keylayouts.h
    7: press_duration in msec (100 msec increments)


    TX Bytes ( 7 ):
    0: Request ID
    1: Tx Byte Count
    2 - 7: usec time that kb press event was sent.
    */
    uint16_t t3_key_symbol;
    uint16_t t3_key_mods;
    // unsigned short for key symbol, unsigned short for modifiers,
    // 1 byte duration (*100 to get msec duration for press)
    char key_event_info[5]={0,0,0,0,0};
    Serial.readBytes(key_event_info,5);

    t3_key_mods = (uint16_t)(key_event_info[2]<<8 | key_event_info[3]);
    Keyboard.set_modifier(t3_key_mods);
    Keyboard.send_now();

    t3_key_symbol = (uint16_t)(key_event_info[0]<<8 | key_event_info[1]);
    Keyboard.set_key1(t3_key_symbol);
    Keyboard.send_now();

    since_key1_press = 0;
    key1_msec_dur=(unsigned int)(((byte)key_event_info[4])*100);
}
#else
void handleGenerateKeyboardEventRx(byte request_type,byte request_id,byte request_rx_byte_count){
    char key_event_info[5]={0,0,0,0,0};
    Serial.readBytes(key_event_info,5);
    // Do nothing since keyboard support was not enabled at compile time.
}
#endif

//------------------------

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
    byte din_value = 0;
    if (digitalReadFast(6)) din_value |= (1<<0);
    if (digitalReadFast(7)) din_value |= (1<<1);
    if (digitalReadFast(8)) din_value |= (1<<2);
    if (digitalReadFast(9)) din_value |= (1<<3);
    if (digitalReadFast(29)) din_value |= (1<<4);
    if (digitalReadFast(30)) din_value |= (1<<5);
    if (digitalReadFast(31)) din_value |= (1<<6);
    if (digitalReadFast(32)) din_value |= (1<<7);

    tx_byte_buffer[tx_byte_buffer_index]=din_value;
    tx_byte_buffer_index+=1;
}

//------------------------

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
    for (unsigned int i=0;i<sizeof(AIN_PINS);i++){
        v=analogRead(AIN_PINS[i]);
        //ain bits 8..15
        tx_byte_buffer[tx_byte_buffer_index+8+i*2] = (v >> 8) & 0xff;
        //ain time bits 0..7
        tx_byte_buffer[tx_byte_buffer_index+9+i*2] = (v & 0xff);
    }
    tx_byte_buffer_index+=16;
}

//------------------------

void handleSetAnalogThresholdsEventRx(byte request_type,byte request_id,byte request_rx_byte_count){
    /*
    SET_ANALOG_THRESHOLDS: Sets the threshold value for each analog input line.

    RX bytes ( 19 ):
    0: SET_ANALOG_THRESHOLDS
    1: request ID
    2: Rx Byte Count
    3-19: 8 * 16 bit analog input threshold values

    TX Bytes ( 8 ):
    0: Request ID
    1: Tx Byte Count
    2 - 7: usec time that pin was set.
    */
    char threshold_data[sizeof(AIN_PINS)*2];
    Serial.readBytes(threshold_data,sizeof(AIN_PINS)*2);

    for (unsigned int i=0;i<sizeof(AIN_PINS);i++){
        AIN_THRESHOLD_STATES[i]= 0;
        AIN_THRESHOLD_LEVELS[i]=(unsigned int)((threshold_data[i*2] << 8) +
                                                threshold_data[i*2+1]);
    }

}

//------------------------

byte digital_input_streaming_enabled=0;
byte analog_input_streaming_enabled=0;
byte threshold_event_streaming_enabled=0;

void handleEnableInputStreamingRx(byte request_type,byte request_id,byte request_rx_byte_count){
    char inputStreaming[3]={0,0,0};
    Serial.readBytes(inputStreaming,3);
    digital_input_streaming_enabled=inputStreaming[0];
    analog_input_streaming_enabled=inputStreaming[1];
    threshold_event_streaming_enabled=inputStreaming[2];
}

//---------------------------------------
//
// IntervalTimer for reading digital and analog inputs
#define INPUT_LINES_READ_RATE AIN_RATE

byte  last_digital_input_state=0;
byte current_digital_input_state=0;

void inputLineReadTimerCallback(void){
    if (digital_input_streaming_enabled>0){
        addDigitalEventToByteBuffer(); // check for digital input change event
    }

    if (analog_input_streaming_enabled>0 ||
        threshold_event_streaming_enabled>0){
          // Add Analog Input Event
          addAnalogEventToByteBuffer();
    }
}

//----------------------------------------------------
// T3 Generated Events

#define DIGITAL_INPUT_EVENT 1
#define ANALOG_INPUT_EVENT 2
#define THRESHOLD_EVENT 3

#define EVENT_TX_HEADER_COUNT 8
#define DIGITAL_EVENT_TX_BYTE_COUNT 9
#define ANALOG_EVENT_TX_BYTE_COUNT 24
#define THRESHOLD_EVENT_TX_BYTE_COUNT 24

byte addDigitalEventToByteBuffer(){
    // Check for digital input state changes
    current_digital_input_state=0;
    for (byte i=0;i<sizeof(DIN_PINS);i++)
    current_digital_input_state+=(bytePow(2,i)*digitalRead(DIN_PINS[i]));

    updateUsecTime();

    if (current_digital_input_state!=last_digital_input_state){
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
    return 0;
}

byte addAnalogEventToByteBuffer(){

    if (byteBufferFreeSize()<(ANALOG_EVENT_TX_BYTE_COUNT*2))
        return 0;

    unsigned int ain_readings[sizeof(AIN_PINS)];
    for (unsigned int i=0;i<sizeof(AIN_PINS);i++)
        ain_readings[i]=analogRead(AIN_PINS[i]);

    updateUsecTime();

    if (analog_input_streaming_enabled>0){
        tx_byte_buffer[tx_byte_buffer_index]=ANALOG_INPUT_EVENT;
        tx_byte_buffer[tx_byte_buffer_index+1]=ANALOG_EVENT_TX_BYTE_COUNT;
        tx_byte_buffer[tx_byte_buffer_index+2]=t3_usec_time.bytes[0];
        tx_byte_buffer[tx_byte_buffer_index+3]=t3_usec_time.bytes[1];
        tx_byte_buffer[tx_byte_buffer_index+4]=t3_usec_time.bytes[2];
        tx_byte_buffer[tx_byte_buffer_index+5]=t3_usec_time.bytes[3];
        tx_byte_buffer[tx_byte_buffer_index+6]=t3_usec_time.bytes[4];
        tx_byte_buffer[tx_byte_buffer_index+7]=t3_usec_time.bytes[5];

        tx_byte_buffer_index=tx_byte_buffer_index+8;

        for (unsigned int i=0;i<sizeof(AIN_PINS);i++){
            tx_byte_buffer[tx_byte_buffer_index+(i*2)] =
                        (byte)(ain_readings[i] >> 8) & 0xff; //event bits 8..15
            tx_byte_buffer[tx_byte_buffer_index+1+(i*2)] =
                        (byte)(ain_readings[i] & 0xff);    //event bits 0..7
        }
        tx_byte_buffer_index=tx_byte_buffer_index+sizeof(AIN_PINS)*2;
    }

    if (threshold_event_streaming_enabled){
        byte thresh_event_created=0;
        int threshold_triggered_values[sizeof(AIN_PINS)];
        for (unsigned int i=0;i<sizeof(AIN_PINS);i++){
            threshold_triggered_values[i]=0;
            if (AIN_THRESHOLD_LEVELS[i]>0){
                if (ain_readings[i] >= AIN_THRESHOLD_LEVELS[i] &&
                    AIN_THRESHOLD_STATES[i]==0){
                        AIN_THRESHOLD_STATES[i]=1;
                        threshold_triggered_values[i]=ain_readings[i] -
                                                      AIN_THRESHOLD_LEVELS[i];
                        thresh_event_created=1;
                }
                else if (ain_readings[i] < AIN_THRESHOLD_LEVELS[i] &&
                         AIN_THRESHOLD_STATES[i]==1){
                    AIN_THRESHOLD_STATES[i]=0;
                    threshold_triggered_values[i]=ain_readings[i] -
                                                  AIN_THRESHOLD_LEVELS[i];
                    thresh_event_created=1;
                }
            }
        }
        if (thresh_event_created == 1)
            addThresholdEventToByteBuffer(threshold_triggered_values);
    }
    return 0;
}

byte addThresholdEventToByteBuffer(int *threshold_triggered_values){
    /*
    Func doc string TBC
    */

    tx_byte_buffer[tx_byte_buffer_index]=THRESHOLD_EVENT;
    tx_byte_buffer[tx_byte_buffer_index+1]=THRESHOLD_EVENT_TX_BYTE_COUNT;
    tx_byte_buffer[tx_byte_buffer_index+2]=t3_usec_time.bytes[0];
    tx_byte_buffer[tx_byte_buffer_index+3]=t3_usec_time.bytes[1];
    tx_byte_buffer[tx_byte_buffer_index+4]=t3_usec_time.bytes[2];
    tx_byte_buffer[tx_byte_buffer_index+5]=t3_usec_time.bytes[3];
    tx_byte_buffer[tx_byte_buffer_index+6]=t3_usec_time.bytes[4];
    tx_byte_buffer[tx_byte_buffer_index+7]=t3_usec_time.bytes[5];

    tx_byte_buffer_index=tx_byte_buffer_index+8;
    //threshold_triggered_values
    for (unsigned int i=0;i<sizeof(AIN_PINS);i++){
        //event bits 8..15
        tx_byte_buffer[tx_byte_buffer_index+(i*2)] =
                        (byte)(threshold_triggered_values[i] >> 8) & 0xff;
        //event bits 0..7
        tx_byte_buffer[tx_byte_buffer_index+1+(i*2)] =
                        (byte)(threshold_triggered_values[i] & 0xff);
    }

    tx_byte_buffer_index=tx_byte_buffer_index+sizeof(AIN_PINS)*2;
    return 0;
}

//----------------------------------
// Initializer functions for various iosync components.

void initDigitalOutputs(){
    for (unsigned int i=0;i<sizeof(DOUT_PINS);i++){
        pinMode(DOUT_PINS[i], OUTPUT);
        digitalWrite(DOUT_PINS[i], LOW);
    }
    pinMode(STATUS_LED, OUTPUT);
    digitalWrite(STATUS_LED, LOW);
}

void initDigitalInputs(){
    for (unsigned int i=0;i<sizeof(DIN_PINS);i++){
        pinMode(DIN_PINS[i], DIGITAL_INPUT_TYPE);
    }
}

void initAnalogOutput(){
    #ifdef TEENSY_3_1
    analogWriteResolution(12);
    //analogReference(1); //non zero for internal ref gives 1.2v pp
    analogReference(0); //Zero for default/ ext ref gives 3.3v pp
    #endif
}

void initAnalogInputs(){
    for (unsigned int i=0;i<sizeof(AIN_PINS);i++){
        pinMode(AIN_PINS[i], INPUT);
    }
    analogReference(AIN_REF);
    // Analog input bit resolution 10 - 16 bits are supported
    analogReadRes(AIN_RES);
    // HW Analog Input Sample Averaging. 1 = No Averaging to 32 = average
    // 32 samples in HW, max value is 32
    analogReadAveraging(AIN_AVERAGING);
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

    #ifdef TEENSY_3_1
    initAnalogOutput();
    #endif

    sinceLastInputRead=0;
    sinceLastSerialTx=0;

    //# flash ext led 4 times indicating prog start
    for (unsigned int i=0;i<4;i++){
        digitalWrite(STATUS_LED, HIGH);
        delay(350);
        digitalWrite(STATUS_LED, LOW);
        delay(150);
    }
    digitalWrite(STATUS_LED, LOW);
}

//---------------------------------------
// Main loop()
// Repeatedly called while microcontroller is running.
void loop()
{
    if (sinceLastInputRead>=INPUT_LINES_READ_RATE){
        inputLineReadTimerCallback();
        sinceLastInputRead=sinceLastInputRead-INPUT_LINES_READ_RATE;
    }

    handleHostSerialRequests();

    #ifdef KEYBOARD
    if (key1_msec_dur > 0 && since_key1_press >= key1_msec_dur){
        Keyboard.set_modifier(0);
        Keyboard.set_key1(0);
        Keyboard.send_now();
        key1_msec_dur = 0;
    }
    #endif

    if (tx_byte_buffer_index>0 && (byteBufferFreeSize()<24 ||
        sinceLastSerialTx>=MAX_TX_BUFFERING_INTERVAL) ){
            writeByteBufferToSerial();
            Serial.flush();
            Serial.send_now();
            sinceLastSerialTx = sinceLastSerialTx - MAX_TX_BUFFERING_INTERVAL;
    }

}

//------------------------

void handleResetStateRx(byte request_type,byte request_id,byte request_rx_byte_count){
    /*
    */
    sinceLastInputRead=0;
    sinceLastSerialTx=0;

    initDigitalOutputs();

    #ifdef KEYBOARD
    Keyboard.set_modifier(0);
    Keyboard.set_key1(0);
    Keyboard.send_now();
    key1_msec_dur = 0;
    since_key1_press = 0;
    #endif

    analog_input_streaming_enabled=0;
    threshold_event_streaming_enabled=0;
    digital_input_streaming_enabled=0;
    last_digital_input_state=0;
    current_digital_input_state=0;
    for (byte i=0;i<sizeof(DIN_PINS);i++)
        current_digital_input_state+=(bytePow(2,i)*digitalRead(DIN_PINS[i]));
    last_digital_input_state=current_digital_input_state;

    for (byte i=0;i<sizeof(AIN_PINS);i++){
        AIN_THRESHOLD_LEVELS[i]=0;
        AIN_THRESHOLD_STATES[i]=0;
    }

    initUsec48();
    updateUsecTime();

    tx_byte_buffer_index=0;
    tx_byte_buffer[tx_byte_buffer_index]=request_id;
    tx_byte_buffer[tx_byte_buffer_index+1]=request_tx_byte_length[request_type];
    tx_byte_buffer[tx_byte_buffer_index+2]=t3_usec_time.bytes[0];
    tx_byte_buffer[tx_byte_buffer_index+3]=t3_usec_time.bytes[1];
    tx_byte_buffer[tx_byte_buffer_index+4]=t3_usec_time.bytes[2];
    tx_byte_buffer[tx_byte_buffer_index+5]=t3_usec_time.bytes[3];
    tx_byte_buffer[tx_byte_buffer_index+6]=t3_usec_time.bytes[4];
    tx_byte_buffer[tx_byte_buffer_index+7]=t3_usec_time.bytes[5];
    tx_byte_buffer_index=tx_byte_buffer_index+8;
}
