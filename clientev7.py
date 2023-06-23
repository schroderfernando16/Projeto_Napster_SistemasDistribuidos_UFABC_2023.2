import socket
import threading
import os

class NapsterClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.download_folder = "downloads"
        self.peer_port = 6000  # Porta para ouvir conexões de outros peers
        self.server_socket = None

    def join_network(self, peer_name, folder_path):
        files = [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]
        files_str = ' '.join(files)
        message = f'JOIN {peer_name} {files_str} {self.peer_port}'
        response = self.send_message(message)
        print(response)

    def search_files(self, search_query):
        message = f'SEARCH {search_query}'
        response = self.send_message(message)
        if response.startswith('peers com arquivo solicitado:'):
            peers_list = response.split(':')[1].strip().split()
            print('Peers com o arquivo solicitado:')
            for peer_address in peers_list:
                print(peer_address)

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.peer_port))
        self.server_socket.listen(5)
        print(f'Servidor do cliente iniciado na porta {self.peer_port}')

        while True:
            client_socket, client_address = self.server_socket.accept()
            thread = threading.Thread(target=self.handle_peer_request, args=(client_socket,))
            thread.start()

    def handle_peer_request(self, client_socket):
        # Receber a mensagem do peer
        message = client_socket.recv(1024).decode()
        message_parts = message.split()
        command = message_parts[0]

        if command == 'DOWNLOAD':
            file_name = message_parts[1]
            self.send_file(file_name, client_socket)
        else:
            response = 'ERROR'
            client_socket.send(response.encode())

        client_socket.close()

    def send_file(self, file_name, client_socket):
        file_path = os.path.join(self.download_folder, file_name)
        # Definir o tipo de mídia como "video/mp4" para arquivos .mp4
        file_type = 'video/mp4'

        # Enviar o cabeçalho com o tipo de mídia correto
        header = f"HTTP/1.1 200 OK\r\nContent-Type: {file_type}\r\n\r\n"
        client_socket.send(header.encode())
        with open(file_path, 'rb') as file:
            data = file.read(1024)
            while data:
                client_socket.sendall(data)
                data = file.read(1024)

    def send_message(self, message, ip=None, port=None, file_path=None):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if ip is None:
            server_address = (self.server_ip, self.server_port)
        else:
            server_address = (ip, port)
        client_socket.connect(server_address)
        client_socket.sendall(message.encode())
        response = client_socket.recv(1024).decode()

        if file_path is not None:
            with open(file_path, 'wb') as file:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    file.write(data)

        client_socket.close()
        return response
    
    def send_dowloand_message(self, message, ip=None, port=None, file_path=None):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if ip is None:
            server_address = (self.server_ip, self.server_port)
        else:
            server_address = (ip, port)
        client_socket.connect(server_address)
        client_socket.sendall(message.encode())
        response = client_socket.recv(1024)

        if file_path is not None:
            with open(file_path, 'wb') as file:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    file.write(data)

        client_socket.close()
        return response
    
    def download_file(self, file_name, peer_address):
        ip, port = peer_address.split(':')
        message = f'DOWNLOAD {file_name}'
        file_path = os.path.join(self.download_folder, file_name)
        self.send_dowloand_message(message, ip, int(port), file_path)

    def close_server(self):
        if self.server_socket:
            self.server_socket.close()

def main():
    client = NapsterClient('localhost', 5000)
    server_thread = None

    while True:
        print('Selecione uma opção:')
        print('1 - Join')
        print('2 - Search Files')
        print('3 - Update')
        print('4 - Fechar o programa')

        option = input('Opção: ')

        if option == '1':
            peer_name = input('Digite o nome do peer: ')
            client.download_folder = input('Digite o caminho da pasta dos arquivos: ')
            client.peer_port = int(input('Insira a porta que seu peer receberá requisições: '))
            client.join_network(peer_name, client.download_folder)
            if not server_thread or not server_thread.is_alive():
                server_thread = threading.Thread(target=client.start_server)
                server_thread.start()
                print('Servidor iniciado.')
            else:
                print('Servidor já está em execução.')
        elif option == '2':
            search_query = input('Digite o termo de busca: ')
            client.search_files(search_query)
            file_name = search_query
            peer_address = input('Digite o endereço IP:porta do peer: ')
            client.download_file(file_name, peer_address)
        elif option == '3':
            print('Opção de atualização selecionada')
            # Implemente a lógica de atualização do cliente aqui
        elif option == '4':
            quit()
        else:
            print('Opção inválida. Tente novamente.')

if __name__ == '__main__':
    main()
