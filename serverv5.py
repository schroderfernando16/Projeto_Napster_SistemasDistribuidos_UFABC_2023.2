#NOME: Fernando Schroder Rodrigues
#RA: 11201921885

import socket

'''Aqui definimos toda a classe de servidor, deixando ele habilitado para receber e armazenar os códigos dos peers'''
class NapsterServer:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.peers = {}
#Função JOIN, o servidor recebe as informações do peer que vai se juntar a rede recebendo, a porta, o Ip e a Pasta que será do peer. 
    def join(self, peer_socket, peer_address, peer_name, files, peer_port):
        self.peers[peer_address] = {'name': peer_name, 'files': files, 'port': peer_port}
        print(f' Peer {peer_address} adicionado com arquivos {files}')
#Função SEARCH, Recebe um arquvo onde ele irá procurar dentro do dicionario de peers qual peer possui o arquivo desejado.
    def search(self, search_query):
        response = ''
        for peer_address, peer_info in self.peers.items():
            files = peer_info['files']
            if search_query in files:
                response += f'{peer_address}'
        return response.strip()
#Função UPDATE, Recebe o arquivo, e atualiza o indice com o novo arquivo baixado    
    def update_peer_files(self, peer_address, file_name):
        if peer_address in self.peers:
            self.peers[peer_address].append(file_name)
        else:
            self.peers[peer_address] = [file_name]


#Função DOWNLOAD, pega o resultado da busca e pede o IP e a Porta em que será feito o Download, em caso de erro o servidor manda mensagem para o peer sobre o erro
    def download(self, peer_address, file_name):
        peer_ip, peer_port = peer_address.split(':')
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_socket.connect((peer_ip, int(peer_port)))
            message = f'DOWNLOAD {file_name}'
            peer_socket.send(message.encode())
            response = peer_socket.recv(1024).decode()

            if response.startswith('ERROR'):
                print(f'Erro ao baixar o arquivo {file_name} do peer {peer_address}')
            else:
                file_path = f'downloads/{file_name}'
                with open(file_path, 'wb') as file:
                    while True:
                        data = peer_socket.recv(1024)
                        if not data:
                            break
                        file.write(data)
        except Exception as e:
            print(f'Erro ao conectar ao peer {peer_address}: {str(e)}')
        finally:
            peer_socket.close()
#Função para fazer o gerenciamento das conexões, foi inspirada em páginas da internet e foruns de dúvidas online (link para o site está no relatório)
    def handle_peer(self, peer_socket, peer_address):
        message = peer_socket.recv(1024).decode()
        message_parts = message.split()
        command = message_parts[0]

        if command == 'JOIN':
            peer_name = message_parts[1]
            files = message_parts[2:-1]
            peer_port = message_parts[-1]
            self.join(peer_socket, peer_address, peer_name, files, peer_port)
            response = 'JOIN_OK'
        elif command == 'SEARCH':
            search_query = message_parts[1]
            print(f'Peer {message_parts[2]} solicitou arquivo {search_query}')
            response = self.search(search_query)
        elif command == 'UPDATE':
                file_name = message_parts[1]
                self.update_peer_files(peer_address, file_name)
                response = 'UPDATE_OK'
        elif command == 'DOWNLOAD':
            file_name = message_parts[1]
            if peer_address in self.peers:
                self.download(peer_address, file_name)
                response = 'DOWNLOAD_OK'
            else:
                response = 'ERROR Peer não encontrado'
        else:
            response = 'ERROR'

        peer_socket.send(response.encode())
        peer_socket.close()

#Main para inicializar o servidor
def main():
    server = NapsterServer('localhost', 5000)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server.server_ip, server.server_port))
    server_socket.listen(5)

    while True:
        peer_socket, peer_address = server_socket.accept()
        server.handle_peer(peer_socket, peer_address)

if __name__ == '__main__':
    main()
