import socket
import threading
import os

#Classe do cliente: o peer vai atuar tanto como um servidor como um peer nesse caso
class NapsterClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.download_folder = "downloads"
        self.peer_port = 1099
        self.server_socket = None
        self.ip= '127.0.0.1'
#Função JOIN do lado do peer, envia para o servidor principal uma requisição com inputs do teclado como nome,porta,ip e caminho da pasta que estão os arquivos.
    def join_network(self, peer_name, folder_path):
        files = [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]
        files_str = ' '.join(files)
        message = f'JOIN {peer_name} {files_str} {self.peer_port}'
        response = self.send_message(message)
        if response == 'JOIN_OK':
            print(f'Sou o Peer {self.ip}:{self.peer_port} com os arquivos {files}')
#Função SEARCH do lado do Peer: aqui o peer irá fazer a requisição de busca do arquivo, ele es'ta trabalhando para ser o nome exto do arquivo já com a extensão
    def search_files(self, search_query):
        message = f'SEARCH {search_query} {self.server_ip}:{self.peer_port}'
        response = self.send_message(message)
        if response == '':
            print("Arquivo não encontrado")
            return 0
        else:
            print(f'Peers com o arquivo solicitado: {response}')
            return 1
#Função para inciar o Peer como um servidor e ele estar disponível para receber conexões TCP
    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.peer_port))
        self.server_socket.listen(5)

        while True:
            client_socket, client_address = self.server_socket.accept()
            thread = threading.Thread(target=self.handle_peer_request, args=(client_socket,))
            thread.start()
#Função para gerenciar as requisões de um peer que quer fazer o download de um arquivo
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
#Manda um arquivo a partir de uma solicitação, aqui para garantir o envio de arquivos MP4 nesse caso foi utilizado o header para garantir que o código rode, ele abrirá o arquivo na forma de binário para fazero envio para o outro peer
    def send_file(self, file_name, client_socket):
        file_path = os.path.join(self.download_folder, file_name)
        # Definir o tipo de mídia como "video/mp4" para arquivos .mp4
        file_type = 'video/mp4'

        #Enviar o cabeçalho com o tipo de mídia correto
        header = f"HTTP/1.1 200 OK\r\nContent-Type: {file_type}\r\n\r\n"
        client_socket.send(header.encode())
        with open(file_path, 'rb') as file:
            data = file.read(1024) #quebrando o arquivo em diversas partes de 1024b
            while data:
                client_socket.sendall(data)
                data = file.read(1024)

#Método para mandar mensagem a um outro servidor, utilizando a parte de sockets
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
#Método especifico para o envio sem fazer o decode, para possibilitar o envio de um arquivo entre 2 pers 
    def send_dowloand_message(self, message, ip=None, port=None, file_path=None,file_name=None):
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
                print(f'Arquivo {file_name} Baixado com sucesso na pasta : {file_path}')

        client_socket.close()
        return response
#Função de Download, onde ele irá mandar a requisão de um peer para o outro fazer o download e após isso irá fazer a requisição de update no servidor principal.    
    def download_file(self, file_name, peer_address):
        ip, port = peer_address.split(':')
        message = f'DOWNLOAD {file_name}'
        file_path = os.path.join(self.download_folder, file_name)
        self.send_dowloand_message(message, ip, int(port), file_path, file_name)
        update_message = f'UPDATE {file_name}'
        self.send_message(update_message, self.server_ip, self.server_port, None)
#Função para fechar o servidor
    def close_server(self):
        if self.server_socket:
            self.server_socket.close()
    

def main():
    client = NapsterClient('localhost', 5000)
    server_thread = None
#Menu interativo com opções
    while True:
        print('Selecione uma opção:')
        print('1 - Join')
        print('2 - Search Files')
        print('3 - Download (somente após uma busca)')
        print('4 - Fechar o programa')

        option = input('Opção: ')

        if option == '1':
            peer_name = input('Digite o nome do peer: ')
            client.download_folder = input('Digite o caminho da pasta dos arquivos: ')
            client.ip = input('Digite o seu IP: ')
            client.peer_port = int(input('Insira a porta que seu peer receberá requisições: '))
            client.join_network(peer_name, client.download_folder)
            if not server_thread or not server_thread.is_alive():
                server_thread = threading.Thread(target=client.start_server)
                server_thread.start()
        elif option == '2':
            search_query = input('Digite o termo de busca: ')
            results = client.search_files(search_query)
            if results == 1:
                file_name = search_query
                option = input('Se deseja fazer o download digite 3 ou qualquer outra tecla para voltar ao menu: ')
                if option == '3':
                    peer_address = input('Digite o endereço IP:porta do peer: ')
                    client.download_file(file_name, peer_address)
        elif option == '4':
           server_thread.join(timeout=1)
           break
        else:
            print('Opção inválida. Tente novamente.')

if __name__ == '__main__':
    main()
