# IoT_SST-to-TTS
Assistive Camera for Low Visions using Google Coral Dev Board

## Overview
There are many people with low vision all around the world. Because of their physical disability, they have difficulties finding objects. In order to help them find their object much easier and more useful, we designed the ‘Assistive Camera for Low Visions’. The main idea of our project is 'User simply speak the stuff what he/she wants to find. After that, the device will tell the location of that stuff'. We expect this device can help low vision people to find their stuff conveniently.


![image](https://user-images.githubusercontent.com/72617445/233795528-bb0ed3b6-f639-41b0-9d97-c441fdcc2d83.png)


## Methodology
### Hardware Architecture
We used Google Coral Dev Board, a webcam, a headset, and a server computer. The webcam we used is capable of both voice input and video streaming simultaneously. We used the headset as a speaker for users to hear the Dev Board's voice, and we utilized a personal laptop computer as a server to quickly process entity recognition.

### Model
We used the MobileNet-SSD-v2 (quantized int8) model trained on the MS-COCO dataset.

### Position Calculation
We divided the position into four zones within the frame of the camera.    
For simplicity, we take the middle point of the bounding box as the position of the object.
  
![image](https://user-images.githubusercontent.com/72617445/233795328-12a13ab5-5ab1-41c9-8de3-2f62b5225f4e.png)

### Importance of multi-threading
Our method requires real-time inference, but there is a delay in recording and sound playback due to the characteristics of Python. To solve this, we divided it into threads for inferring the model, recording, and sound playback, so that there is no burden on real-time detection.

### Reasons for using the server
Konlpy operates on top of the Java Virtual Machine, but there have been problems with the Coral Board due to insufficient RAM memory. Although we tried to use the swap memory settings of the Coral Board to utilize disk space as virtual memory, there was a decrease in speed in real-time named entity recognition. To solve this, we configured it to send input text to the server and perform NER on the server, and then receive the result value back.

-------------
# Usage
## Requirements
- python >= 3.7.3
- pycoral
- cv2, pillow, flask
- pyaudio, wave, gtts, pydub, playsound
- socket
- konlpy, requests, kakao-STT
- threading, queue

## API
- STT
  - [Kakao speech-to-text API](https://speech-api.kakao.com/)
  - To convert recorded audio file to text
- NER
  - [Kkma](http://kkma.snu.ac.kr/)
  - To find the object(noun) among the text
  - Kkma is a morphological analyzer developed for natural language processing tasks in the Seoul National University IDS lab. Although its inference time is slow, its accuracy is good. We use Kkma, which has good accuracy, because we perform NER on the server.
- TTS
  - [Google text-to-speech module](https://pypi.org/project/gTTS/)
  - To tell the location of the object


------------
## Contributor
- Soonki Kwon, kwonrince@gmail.com
- Hyunho Lee, lake8000@ds.seoultech.ac.kr
- Boyoung Han, byhan2253@ds.seoultech.ac.kr
