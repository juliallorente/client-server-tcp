import socket, os, time

class Client:
    
    IP = socket.gethostbyname(socket.gethostname())
    PORT = 8888
    BROADCAST_PORT = 4451
    ADDR = (IP, PORT)
    FORMAT = "utf-8"
    SIZE = 1024
    TIMEOUT = 5
    
    def __init__(self, **kwargs):
        
        self.COMMANDS = {
            "help": self.send_help,
            "exit": self.exit,
            "list": self.list_files,
            "delete": self.delete_file,
            "upload": self.upload_file,
            "download": self.download_file
        }
        
        try:
            self.ADDR = self.get_addr(**kwargs)
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(self.ADDR)
            self.cli(**kwargs)
        except ConnectionRefusedError:
            print("Não foi possível se conectar ao servidor. Verifique se o servidor está rodando e acessível.")
        except Exception as e:
            print(f"Um erro inesperado aconteceu, desligando o cliente: {e}")
        
    def cli(self, **kwargs):
        while True:
            if not self.is_status_ok(self.client.recv(self.SIZE).decode(self.FORMAT)):
                break
            data = input("> ")
            data = data.split(" ")
            cmd = data[0]
            
            if cmd in self.COMMANDS:
                self.COMMANDS[cmd](data)
            else:
                print("COMANDO INVALIDO - SAINDO")
                break
        
        print("Disconectado do Servidor.")
        self.client.close()

    def is_status_ok(self, data):
        cmd, msg = data.split("@")

        if cmd == "DISCONNECTED":
            print(f"[SERVER]: {msg}")
            return False
        elif cmd == "OK":
            print(f"{msg}")
            return True
    
    def get_addr(self, **kwargs):
        ip = self.IP
        port = self.PORT
        addr = (ip, port) 
        
        if 'connection_type' in kwargs:
            if kwargs['connection_type'] == 'LAN':
                addr = self.get_lan_addr(**kwargs)
                print(f"Conexão LAN: {addr}")
                return addr 
            elif kwargs['connection_type'] == 'WAN':
                addr = self.get_wan_addr(**kwargs)
                print(f"Conexão WAN: {addr}")
                return addr
        
        print(f"Conexão Local: {addr}")
        return addr
    
    def get_lan_addr(self, **kwargs):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(self.TIMEOUT)

        try:
            sock.sendto("REQUERIMENTO_DE_DESCOBERTA_DE_SERVER".encode(), ('<broadcast>', self.BROADCAST_PORT))

            start_time = time.time()
            while True:
                try:
                    data, addr = sock.recvfrom(1024)
                    if data.decode() == "RESPOSTA_DE_DESCOBERTA_DE_SERVER":
                        print(f"Servidor encontrado em {addr[0]}")
                        return (addr[0], self.PORT)
                except socket.timeout:
                    print("Tempo limite de espera excedido.")
                    break

                if time.time() - start_time > self.TIMEOUT:
                    print("Tempo limite de busca pelo servidor excedido.")
                    break
        finally:
            sock.close()
    
    def get_wan_addr(self, **kwargs):
        if 'IP' and 'PORT' in kwargs:
            return (kwargs['IP'], int(kwargs['PORT']))
        raise ConnectionAbortedError('Por favor, para usar WAN indique o IP e o PORT')
    
    def send_help(self, data):
        self.client.send("help".encode(self.FORMAT))

    def exit(self, data):
        self.client.send("exit".encode(self.FORMAT))
        print("Saindo.")
        self.client.close()
        exit(0)

    def list_files(self, data):
        self.client.send("list".encode(self.FORMAT))

    def delete_file(self, data):
        filename = data[1]
        self.client.send(f"delete@{filename}".encode(self.FORMAT))

    def upload_file(self, data):
        path = data[1]
        with open(path, "r") as f:
            text = f.read()
        filename = path.split("/")[-1]
        send_data = f"upload@{filename}@{text}"
        self.client.send(send_data.encode(self.FORMAT))

    def download_file(self, data):
        file_name = data[1]
        download_path = os.path.join(data[2], file_name) if len(data) > 2 else file_name
        self.client.send(f"download@{file_name}".encode(self.FORMAT))

        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        with open(download_path, "wb") as f:
            while True:
                bytes_read = self.client.recv(self.SIZE)
                if bytes_read.endswith(b"OK@"):
                    f.write(bytes_read[:-3])
                    break
                f.write(bytes_read)
        print(f"File {file_name} downloaded to {download_path} successfully.")

if __name__ == "__main__":
    Client()
