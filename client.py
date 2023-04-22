import socket
import threading, queue

ner_queue = queue.Queue()
text = '자전거는 어디에있나요?'

def client(text):
    global ner_queue
    # 접속 정보 설정
    SERVER_IP = '192.168.0.19'
    SERVER_PORT = 5050
    SIZE = 1024
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)
    text = text
    
    # 클라이언트 소켓 설정
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(SERVER_ADDR)  # 서버에 접속
        client_socket.send(text.encode())  # 서버에 메시지 전송
        text = client_socket.recv(SIZE)  # 서버로부터 응답받은 메시지 반환
        text = str(text, 'utf-8')
        ner_queue.put(text)
        print("resp from server : {}".format(text))  # 서버로부터 응답받은 메시지 출력

T4 = threading.Thread(target=client, name='client', args=(text,))
T4.start()

ner_text = ner_queue.get()
