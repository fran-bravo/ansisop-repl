#include <stdio.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>
#include "commons/string.h"

#define MAX_CONNECTION_SERVER 60

typedef struct {
    uint8_t tipo;
    uint16_t length;
} t_socketHeader;

typedef uint8_t t_tipoEstructura;

typedef struct {
    uint8_t tipoEstructura;
    uint16_t length;
} __attribute__ ((__packed__)) t_header;

typedef struct struct_string {
    char * string;
} __attribute__ ((__packed__)) t_struct_string;

int socket_aceptarCliente(int socketEscucha);
int socket_crearServidorIpLocal(int port);
int socket_recibir(int socketEmisor, t_tipoEstructura * tipoEstructura, void** estructura);
int socket_cerrarConexion(int socket);

t_struct_string * despaquetizarStruct_string(char * dataPaquete, uint16_t length);
t_header despaquetizarHeader(char * header);


int sock_servidor;


int main() {
    if((sock_servidor=socket_crearServidorIpLocal(5000))>0){
        printf("Hilo de Conexiones\n");
    }

    int sock_aceptado;

    t_tipoEstructura tipoRecibido;
    void* structRecibida;

    if((sock_aceptado=socket_aceptarCliente(sock_servidor))>0){
        printf("Acepta conexion\n");
    }

    while(1){
        socket_recibir(sock_aceptado, &tipoRecibido, &structRecibida);
        t_struct_string* lineaRecibida = ((t_struct_string*)structRecibida);

	    printf("String despaquetizado: %s\n", lineaRecibida->string); //Reemplazar por funcion que maneje lo recibido
        if(string_contains(lineaRecibida->string, "exit")) break;
        free(structRecibida);
    }

    socket_cerrarConexion(sock_aceptado);
}


int socket_crearServidorIpLocal(int port){
    int socketEscucha;
    struct sockaddr_in miSocket;

    if((socketEscucha = socket(AF_INET,SOCK_STREAM,0)) == -1){
        perror("Error al crear socket");
        return -1;
    }

    miSocket.sin_family = AF_INET;
    miSocket.sin_port = htons(port);
    miSocket.sin_addr.s_addr = INADDR_ANY;
    memset(&(miSocket.sin_zero),'\0',8);

    int yes = 1;

    if (setsockopt(socketEscucha, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) == -1) {
        perror("setsockopt");
        exit(1);
    }

    if(bind(socketEscucha,(struct sockaddr*)&miSocket, sizeof(miSocket)) == -1){
        perror ("Error al bindear el socket escucha");
        return -1;
    }

    if (listen(socketEscucha, MAX_CONNECTION_SERVER) == -1){
        perror("Error en la puesta de escucha");
        return -1;
    }

    return socketEscucha;
}


int socket_aceptarCliente(int socketEscucha){
    int socketNuevaConexion;
    unsigned int size_sockAddrIn;

    struct sockaddr_in suSocket;

    size_sockAddrIn = sizeof(struct sockaddr_in);
    socketNuevaConexion = accept(socketEscucha, (struct sockaddr *)&suSocket, &size_sockAddrIn);

    if(socketNuevaConexion < 0) {
        perror("Error al aceptar conexion entrante");
        return -1;
    }

    return socketNuevaConexion;
}


int socket_recibir(int socketEmisor, t_tipoEstructura * tipoEstructura, void** estructura){
    int cantBytesRecibidos;
    t_header header;
    char* buffer;
    char* bufferHeader;

    bufferHeader = malloc(sizeof(t_header));

    cantBytesRecibidos = recv(socketEmisor, bufferHeader, sizeof(t_header), MSG_WAITALL);

    if(cantBytesRecibidos == -1){
        free(bufferHeader);
        perror("Error al recibir datos\n");
        return 0;
    }

    header = despaquetizarHeader(bufferHeader);
    free(bufferHeader);

    if (tipoEstructura != NULL) {
        *tipoEstructura = header.tipoEstructura;
    }

    if(header.length == 0){
        if (estructura != NULL) {
            *estructura = NULL;
        }
        return 1;
    }

    buffer = malloc(header.length);
    cantBytesRecibidos = recv(socketEmisor, buffer, header.length, MSG_WAITALL);

    if(cantBytesRecibidos == -1){
        free(buffer);
        perror("Error al recibir datos\n");
        return 0;
    }

    if(estructura != NULL) {
        *estructura = despaquetizarStruct_string(buffer, header.length);
    }

    free(buffer);

    if (cantBytesRecibidos == 0){
        *tipoEstructura = 0;
    }

    return 1;
}


int socket_cerrarConexion(int socket){
    return close(socket);
}


t_struct_string * despaquetizarStruct_string(char * dataPaquete, uint16_t length){
    t_struct_string * estructuraDestino = malloc(sizeof(t_struct_string));

    int tamanoTotal = 0, tamanoDato = 0;

    tamanoTotal = tamanoDato;

    for(tamanoDato = 1; (dataPaquete + tamanoTotal)[tamanoDato -1] != '\0';tamanoDato++);

    estructuraDestino->string = malloc(tamanoDato);
    memcpy(estructuraDestino->string, dataPaquete + tamanoTotal, tamanoDato);

    return estructuraDestino;
}


t_header despaquetizarHeader(char * header){
    t_header estructuraHeader;

    int tamanoTotal = 0, tamanoDato = 0;
    memcpy(&estructuraHeader.tipoEstructura, header + tamanoTotal, tamanoDato = sizeof(uint8_t));
    tamanoTotal = tamanoDato;
    memcpy(&estructuraHeader.length, header + tamanoTotal, tamanoDato = sizeof(uint16_t));

    return estructuraHeader;
}
