#include <sys/types.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netdb.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include<iostream>
#include<vector>
#include <string>

using namespace std;

#define QUEUE_SIZE 5
#define NUMBER_OF_USERS 32
#define NAME_LENGTH 1024



pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

struct user_t {
    int socket;
    char name[NAME_LENGTH];
};

struct thread_data_t {
    int socket;
    int user_counter; 
    char incoming_message[1024];
    int bytes_read;
};

struct user_t users[NUMBER_OF_USERS];

void deleteUser(int user_id) {
    if (user_id >= 0) {
        users[user_id].socket = -1;
        memset(users[user_id].name, 0, sizeof(users[user_id].name));
}
}
//pierwszy wolny socket
int freesocket() {
    for (int i=0; i<NUMBER_OF_USERS; i++)
        if (users[i].socket == -1)
            return i;
    return -1;
}

void *Thread_Listening(void *t_data) {
        pthread_detach(pthread_self());
        struct thread_data_t *th_data = (struct thread_data_t*)t_data;
        while(1) {
            memset((*th_data).incoming_message, 0, sizeof((*th_data).incoming_message));
            (*th_data).bytes_read = recv((*th_data).socket, (*th_data).incoming_message,sizeof((*th_data).incoming_message),0);

            if ((*th_data).bytes_read > 0) {

                if ((*th_data).incoming_message[0] == '#') { //wiadomosc #od:do:wiadomosc$
                    pthread_mutex_lock(&mutex); //sekcja krytyczna
                    //wydobycie z calej wiadomosci "do", zeby wyslac ja tylko do adresata (znalezc najpierw
                    int w=1;
                    char to[1024];
                    to[0]='*';
                    while((*th_data).incoming_message[w]!=':')
                    {
                      w++;
                    }
                    w++;
                    int v = 1;
                    while((*th_data).incoming_message[w]!=':')
                    {
                      to[v] = (*th_data).incoming_message[w];
                      //cout<<(*th_data).incoming_message[w]<<endl;
                      w++;
                      v++;
                    }
                    to[v]='$';
                    cout<<"to "<<to<<endl; //"to" to do z dodanym $ przed i # za, zeby sie zgadzalo z forma zapisana w users
                    for (int i=0; i<NUMBER_OF_USERS; i++) { //znalezienie "to" w users i wyslanie do niego wiadomosci
                        if (strcmp(to,users[i].name)==0) {
                            send(users[i].socket, (*th_data).incoming_message, 1024,0);
                     }
                   }
                 }
                 else if ((*th_data).incoming_message[0] == '*') { // wiadomosc z nowym uzytkownikiem *login$
                    pthread_mutex_lock(&mutex); //sekcja krytyczna
//cout<<(*th_data).incoming_message;
                    for (int i=0;i<=NUMBER_OF_USERS;i++){
                        if (users[i].socket == (*th_data).socket){
                            for(int k=0;k<(*th_data).bytes_read;k++){
                            users[i].name[k]=(*th_data).incoming_message[k];} //wpisanie nazwy nowego uzytkownika do users
                            for (int j=0; j<NUMBER_OF_USERS; j++) {
                             if (users[j].socket != -1 && users[j].socket != users[i].socket ) { //wyslanie wiadomosci z nowym uzytkownikiem do starych klientow i 
//nazw starych uzytkownikow do nowych, zeby wszyscy mieli siebie w kontaktach
                                cout<<"wyslano do starych "<<(*th_data).incoming_message<<endl;
                                send(users[j].socket, (*th_data).incoming_message, 1024,0);
                                cout<<"wyslano do nowego "<<users[j].name<<endl;
                                send(users[i].socket, users[j].name, 1024,0);
                     }
                   }
                  }



}
//wyswietlenie w terminalu uzytkownikow z users, zeby sprawdzic czy dziala poprawnie
for(int d=0;d<=NUMBER_OF_USERS;d++){
cout<<"w tab sa "<<users[d].name<<endl;
}
}
        }
pthread_mutex_unlock(&mutex); //wyjscie z sekcji krytycznej
    }
            free(t_data);
            pthread_exit(NULL);
    }


void handleConnection(int connection_socket_descriptor) {
    pthread_mutex_lock(&mutex);
    int user_counter = freesocket();
    if (user_counter != -1) {
        users[user_counter].socket = connection_socket_descriptor;
        cout<<"Nowy uzytkownik: "<<user_counter<<" "<<NUMBER_OF_USERS-1<<endl;
        pthread_t thread1;
        struct thread_data_t *t_data1;
        t_data1 = new thread_data_t;
        t_data1->socket = connection_socket_descriptor;
        t_data1->user_counter = user_counter;
        if (pthread_create(&thread1, NULL, Thread_Listening, (void *)t_data1)) {
            printf("Błąd - tworzenie wątku\n");
            exit(1);
        };
    } else close(connection_socket_descriptor);
    pthread_mutex_unlock(&mutex);
}




int main(int argc, char*argv[]) {

    int port_num;
    int server_socket_descriptor;
    int connection_socket_descriptor;
    char reuse_addr_val = 1;
    struct sockaddr_in server_address;

    int i;
    //numeru portu z argv[1]
    if (argc < 2) {
        printf("Port: \n");
        exit(1);
    } else {
        sscanf (argv[1],"%d",&port_num);
    }

    memset(&server_address, 0, sizeof(struct sockaddr));
    server_address.sin_family = AF_INET;
    server_address.sin_addr.s_addr = htonl(INADDR_ANY);
    server_address.sin_port = htons(port_num);
    server_socket_descriptor = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket_descriptor < 0) {
        fprintf(stderr, "%s: Błąd - tworzenie socketu\n", argv[0]);
        exit(1);
    }
    setsockopt(server_socket_descriptor, SOL_SOCKET, SO_REUSEADDR, (char*)&reuse_addr_val, sizeof(reuse_addr_val));

    if (bind(server_socket_descriptor, (struct sockaddr*)&server_address, sizeof(struct sockaddr)) < 0){
        fprintf(stderr, "%s: Błąd - dowiązanie adresu i portu do socketu\n", argv[0]);
        exit(1);
    }

    if (listen(server_socket_descriptor, QUEUE_SIZE) < 0){
        fprintf(stderr, "%s: Błąd kolejka\n", argv[0]);
        exit(1);
    }

    for (i=0; i<NUMBER_OF_USERS; i++) deleteUser(i);

    while(1) {
        connection_socket_descriptor = accept(server_socket_descriptor, NULL, NULL);
        if (connection_socket_descriptor < 0) {
            fprintf(stderr, "%s: Błąd przy tworzeniu socketu\n", argv[0]);
            exit(1);
        }

        handleConnection(connection_socket_descriptor);

    }

    close(server_socket_descriptor);
    return(0);

}
