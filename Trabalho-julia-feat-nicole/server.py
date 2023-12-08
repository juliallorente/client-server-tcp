import socket, time

import os
import threading

class Server:
    
    IP = ''
    PORT = 8888
    BROADCAST_PORT = 4451
    ADDR = (IP, PORT)
    SIZE = 1024
    FORMAT = "utf-8"
    SERVER_DATA_PATH = "server_data"
    
    def __init__(self, **kwargs):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.ADDR)
                
        self.COMMANDS = {
            "list": self.list,
            "upload": self.upload,
            "delete": self.delete,
            "download": self.download,
            "exit": self.exit,
            "help": self.help
        }
        
        broadcast_listener = threading.Thread(target=self.broadcast_listener, kwargs=kwargs)
        broadcast_listener.start()
        
        self.listener(**kwargs)

        
    def broadcast_listener(self, **kwargs):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.BROADCAST_PORT))
        print('Serviço de IP por Broadcast Online')

        while True:
            data, addr = sock.recvfrom(1024)
            if data.decode() == "REQUERIMENTO_DE_DESCOBERTA_DE_SERVER":
                response = "RESPOSTA_DE_DESCOBERTA_DE_SERVER"
                sock.sendto(response.encode(), addr)
        
    def listener(self, **kwargs):
        self.server.listen()
        print(f"[LISTENING] Server is listening on {self.IP}:{self.PORT}.")

        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr), kwargs=kwargs)
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

    def handle_client(self, conn, addr, **kwargs):
        print(f"[NEW CONNECTION] {addr} connected.")
        conn.send("OK@Welcome to the File Server.".encode(self.FORMAT))

        while True:
            data = conn.recv(self.SIZE).decode(self.FORMAT)
            data = data.split("@")
            cmd = data[0]
            
            if cmd in self.COMMANDS:
                if self.COMMANDS[cmd](conn, data, addr):
                    break

    def list(self, *args, **kwargs):
        conn, data,  addr = args
        files = os.listdir(self.SERVER_DATA_PATH)
        send_data = "OK@"

        if len(files) == 0:
            send_data += "The server directory is empty"
        else:
            send_data += "\n".join(f for f in files)
        conn.send(send_data.encode(self.FORMAT))

    def upload(self, *args, **kwargs):
        conn, data,  addr = args
        name, text = data[1], data[2]
        filepath = os.path.join(self.SERVER_DATA_PATH, name)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(text)

        send_data = "OK@File uploaded successfully."
        conn.send(send_data.encode(self.FORMAT))

    def delete(self, *args, **kwargs):
        conn, data,  addr = args
        files = os.listdir(self.SERVER_DATA_PATH)
        send_data = "OK@"
        filename = data[1]

        if len(files) == 0:
            send_data += "The server directory is empty"
        else:
            if filename in files:
                os.system(f"rm {self.SERVER_DATA_PATH}/{filename}")
                send_data += "File deleted successfully."
            else:
                send_data += "File not found."

        conn.send(send_data.encode(self.FORMAT))

    def download(self, *args, **kwargs):
        conn, data, addr = args
        send_data = "OK@"

        # data[1] deve conter o nome do arquivo que o cliente deseja baixar
        filename = data[1]

        filepath = os.path.join(self.SERVER_DATA_PATH, filename)
        
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                file_data = f.read(self.SIZE)
                while file_data:
                    conn.send(file_data)
                    file_data = f.read(self.SIZE)

            conn.send("OK@".encode(self.FORMAT))
            print(f"[FILE SENT] {filename} was sent to {addr}.")
        else:
            send_data += "OK@File not found."
            conn.send(send_data.encode(self.FORMAT))

    def exit(self, *args, **kwargs):
        conn, data,  addr = args
        print(f"[DISCONNECTED] {addr} disconnected")
        conn.close()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        return 1

    def help(self, *args, **kwargs):
        conn, data, addr = args
        help_data = "OK@"
        help_data += "list: Lista todos os arquivos do servidor.\n"
        help_data += "upload <nome do arquivo> <dados>: Faz o upload de um arquivo para o servidor.\n"
        help_data += "delete <nome do arquivo>: Deleta um arquivo do servidor.\n"
        help_data += "download <nome do arquivo> <caminho de destino>: Baixa um arquivo do servidor para o caminho especificado.\n"
        help_data += "exit: Desconecta do servidor.\n"
        help_data += "help: Lista todos os comandos disponíveis."

        conn.send(help_data.encode(self.FORMAT))


if __name__ == "__main__":
    Server()
