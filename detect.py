import os, queue, requests, threading, argparse, io, socket
from flask import Flask, render_template, Response, request, redirect
import cv2

from pycoral.adapters import common
from pycoral.adapters.detect import get_objects
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter

import pyaudio, wave
from playsound import playsound

from gtts import gTTS
from pydub import AudioSegment

from label_list import convertK2V

#%%
class STT(threading.Thread):
    def __init__(self, args, audio_q, q):
        threading.Thread.__init__(self)
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 48000
        self.CHUNK = 1024
        self.SAMPLE_WIDTH = 2
        self.audio = pyaudio.PyAudio()
        self.args = args
        self.headers = {#Transfer-Encoding: chunked # 보내는 양을 모를 때 헤더에 포함한다.
                        'Host': 'kakaoi-newtone-openapi.kakao.com',
                        'Content-Type': 'application/octet-stream',
                        'X-DSS-Service': 'DICTATION',
                        'Authorization': f'KakaoAK {REST API KEY}', # must change
                        }
        self.labels_dict = convertK2V()
        self.audio_q = audio_q
        self.q = q

    def run(self):
        global instance
        global text
        global count
        
        audio_data = self.record(record_seconds=3)
        wav_data = self.getWav(audio_data)
        wav_data = self.convertTo16K(wav_data)
        
        text = self.getText()
        instance = self.labels_dict[text]
        count = 0
        
        self.audio_q.put((text, instance))
        self.q.put(0)
        
        return text, instance


    def record(self, record_seconds):
        stream = self.audio.open(input_device_index=self.args.mic_port,
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK)
     
        print("Start to record the audio.")
     
        frames = []
        for i in range(0, int(self.RATE / self.CHUNK * record_seconds)):
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)
     
        print("Recording is finished.")
        stream.stop_stream()
        stream.close()
        self.audio.terminate()
     
        return frames
     
    def convertTo16K(self, file):
        sound = AudioSegment.from_file(file)
        sound = sound.set_frame_rate(16000)
        rec_data = io.BytesIO()
        sound.export(rec_data, format="wav")
        sound.export("temp.wav", format="wav")
        
        return rec_data
     
    def getWav(self, frames):
        wavfile = io.BytesIO()
        wf = wave.open(wavfile, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.SAMPLE_WIDTH)
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wavfile.seek(0)
        
        return wavfile
        
    def getText(self):
        data = open("temp.wav", "rb").read()
        response = requests.post('https://kakaoi-newtone-openapi.kakao.com/v1/recognize', headers=self.headers, data=data)
        text_ = response.text
        text_ = text_.split('finalResult","value":"')[1]
        text_ = text_.split('",')[0]
        text = client(text_)

        print('Ner 결과 : ', text)
        
        return text

class TTS():
    def __init__(self, text, left_down=None, left_up=None, right_down=None, right_up=None, middle=None):
        self.text = text
        if left_down==True:
            self.speak(self.text+"는 왼쪽 아래에 있어요.")
        if left_up==True:
            self.speak(self.text+"는 왼쪽 위에 있어요.")
        if right_down==True:
            self.speak(self.text+"는 오른쪽 아래에 있어요.")
        if right_up==True:
            self.speak(self.text+"는 오른쪽 위에 있어요.")
        if middle==True:
            self.speak(self.text+"는 가운데에 있어요.")
        
    def speak(self, text): 
        tts = gTTS(text = text, lang='ko')
        tts.save('voice.mp3')
        print("saved done!!!!")
    
def play(x0, y0, x1, y1, text):
    left_up, left_down, right_up, right_down, middle = None, None, None, None, None
    if ((x0+((x1 - x0) / 2)) < 320) and ((y0+((y1 - y0) / 2)) < 240): # left-up
        left_up = True
    if ((x0+((x1 - x0) / 2)) < 320) and ((y0+((y1 - y0) / 2)) > 240): # left-down
        left_down = True
    if ((x0+((x1 - x0) / 2)) > 320) and ((y0+((y1 - y0) / 2)) < 240): # right-up
        right_up = True
    if ((x0+((x1 - x0) / 2)) > 320) and ((y0+((y1 - y0) / 2)) > 240): # right-down
        right_down = True
    # if ((x0+((x1 - x0) / 2)) > 300) and ((x0+((x1 - x0) / 2)) < 340): # middle
    #     middle = True
    print(left_down, left_up, right_down, right_up, middle)
    TTS(text, left_down=left_down, left_up=left_up, right_down=right_down, right_up=right_up, middle=middle)
    print(text+"TTS 파일 생성")
    playsound('voice.mp3', block=True)

# def beepsound():
#     fr = 2000    # range : 37 ~ 32767
#     du = 1000     # 1000 ms ==1second
#     sd.Beep(fr, du) # winsound.Beep(frequency, duration)

def play_start_sound(args, audio_q, q):
    playsound('start.mp3', block=True)
    T2 = STT(args=args, audio_q=audio_q, q=q)
    T2.start()

def client(text_):
    # 접속 정보 설정
    SERVER_IP = args.server_ip
    SERVER_PORT = 5050
    SIZE = 1024
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)
    
    # 클라이언트 소켓 설정
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(SERVER_ADDR)  # 서버에 접속
        client_socket.send(text_.encode())  # 서버에 메시지 전송
        get_text = client_socket.recv(SIZE)  # 서버로부터 응답받은 메시지 반환
        get_text = str(get_text, 'utf-8')
        print("resp from server : {}".format(get_text))  # 서버로부터 응답받은 메시지 출력
    
    return get_text

app = Flask(__name__)

@app.route("/")
def index() :
    return render_template('index.html')

# 라벨 텍스트 dict 형식으로 변환하기
def getLabels(labelPath) :
    with open(labelPath) as f :
        lines = [line.strip().split() for line in f.readlines()]
        lines = [[line[0], line[1]]for line in lines]
        return {int(key) : value for key, value in lines}

def append_objs_to_img(cv2_im, inference_size, objs, labels):
    height, width, channels = cv2_im.shape
    scale_x, scale_y = width / inference_size[0], height / inference_size[1]
    for obj in objs:
        bbox = obj.bbox.scale(scale_x, scale_y)
        x0, y0 = int(bbox.xmin), int(bbox.ymin)
        x1, y1 = int(bbox.xmax), int(bbox.ymax)

        percent = int(100 * obj.score)
        label = '{}% {}'.format(percent, labels.get(obj.id, obj.id))

        cv2_im = cv2.rectangle(cv2_im, (x0, y0), (x1, y1), (0, 255, 0), 2)
        cv2_im = cv2.putText(cv2_im, label, (x0, y0+30),
                             cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)
    return cv2_im

def get_frame() :
    
    interpreter = make_interpreter(modelPath)
    interpreter.allocate_tensors()
    labels = read_label_file(labelPath)
    size = common.input_size(interpreter)

    cap = cv2.VideoCapture(1)
    
    global count
    global text
    global instance
    q = queue.Queue()
    audio_q = queue.Queue()
    
    while cap.isOpened():
        ret, frame = cap.read()

        cv2_im = frame
        cv2_im_rgb = cv2.cvtColor(cv2_im, cv2.COLOR_BGR2RGB)
        cv2_im_rgb = cv2.resize(cv2_im_rgb, size)
        
        common.set_input(interpreter, cv2_im_rgb)
        interpreter.invoke()

        objs = get_objects(interpreter, 0.5)[:3]
        
        cv2_im = append_objs_to_img(cv2_im, size, objs, labels)
        
        height, width, channels = cv2_im.shape
        scale_x, scale_y = width / size[0], height / size[1]

        imgencode = cv2.imencode('.jpg', cv2_im)[1]
        stringData = imgencode.tostring()
        yield (b'--frame\r\n'
                b'Content-Type: text/plain\r\n\r\n' + stringData + b'\r\n')
        
        if count == 0:
            for obj in objs:
                if labels.get(obj.id, obj.id)==instance:
                    print("개체 인식 성공")
                    bbox = obj.bbox.scale(scale_x, scale_y)
                    x0, y0 = int(bbox.xmin), int(bbox.ymin)
                    x1, y1 = int(bbox.xmax), int(bbox.ymax)

                    audio_q = queue.Queue()
                    q = queue.Queue()
                    
                    print("위치 보이스 플레이")
                    T3 = threading.Thread(target=play, name='AudioThread', args=(x0, y0, x1, y1, text))
                    T3.start()
                    print("위치 보이스 플레이 종료")
                    count = 1
                    
        print("q size: ", q.qsize())
        if q.qsize() == 1:
            text, instance = audio_q.get()
            count = q.get()
        print("text : {}, instance: {}".format(text, instance))
        print("count: ", count)
        
    del(cap)

@app.route('/calc')
def calc() :
    return Response(get_frame(),
            mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/run', methods=['GET', 'POST'])
def run():
    global count
    global audio_q
    global q
    global args
    
    audio_q = queue.Queue()
    q = queue.Queue()
    T1 = threading.Thread(target=play_start_sound, name='AudioStartSound', args=(args, audio_q, q)) # or target=beepsound
    
    if request.method == 'POST':
        count = request.form['msg']
    T1.start()

    print("******************시작합니다.******************")
    
    return redirect('/')


if __name__ == "__main__" :
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='tflite model name', type=str, default='/models/mobilenet_ssd_v2__coco_quant_postprocess_edgetpu.tflite')
    parser.add_argument('--labels', help='label file name', type=str, default='/models/coco_labels.txt')
    parser.add_argument('--mic_port', help='mic port', type=int)
    parser.add_argument('--server_ip', help='server ip address', type=str)
    args = parser.parse_args()
    
    modelPath = os.path.join(os.getcwd(), args.model)
    labelPath = os.path.join(os.getcwd(), args.labels)
    
    audio_q = queue.Queue()
    count = 1
    text = None
    instance = None
    
    print("카메라 실행중입니다. 잠시 기다려주세요.")
    
    app.run(host="0.0.0.0", debug=True, threaded=True, use_reloader=False)
