import socket

try:
    ip = socket.gethostbyname("api.dashscope.ai")
    print("IP-адрес:", ip)
except socket.gaierror:
    print("Не удалось разрешить доменное имя")