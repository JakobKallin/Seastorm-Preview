#ifndef RTLD_NEXT
#  define _GNU_SOURCE
#endif
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>

int socket(int domain, int type, int protocol);
int bind(int socket, const struct sockaddr *address,
         socklen_t address_len);
int accept(int socket, struct sockaddr *address,
           socklen_t *address_len);
int connect(int socket, const struct sockaddr *address,
            socklen_t address_len);
int listen(int socket, int backlog);
int shutdown(int socket, int how);
int setsockopt(int socket, int level, int option_name,
               const void *option_value, socklen_t option_len);


int socket(int domain, int type, int protocol)
{
  /*
   * Define the libc_socket and the socket file descriptor
   */
  int (*libc_socket)(int, int, int);
  int sockfd;

  /*
   * Retrieve the actual socket function, and assign it
   * to the libc_socket address
   */ 
  *(void **)(&libc_socket) = dlsym(RTLD_NEXT, "socket");
  if(dlerror()) {
    errno = EACCES;
    return -1;
  }

  /*Create the socket object. */
  sockfd = (*libc_socket)(domain, type, protocol);
  
  printf("\n[DY_PROXY_INFO] Created socket '%d' with domain:%d, type:%d, protocol:%d.", sockfd, domain, type, protocol);

  return sockfd;
} 

    
int bind(int sockfd, const struct sockaddr *address, socklen_t address_len)
{
  int (*libc_bind)(int, const struct sockaddr*, socklen_t);
  int bind_value;

  *(void **)(&libc_bind) = dlsym(RTLD_NEXT, "bind");
  if(dlerror()) {
    errno = EACCES;
    return -1;
  }

  bind_value = (*libc_bind)(sockfd, address, address_len);

  struct sockaddr_in *theiraddr = (struct sockaddr_in *) address;
  char ip_addr[INET_ADDRSTRLEN];
  short port_number = theiraddr->sin_port; 
  
  inet_ntop(AF_INET, &(theiraddr->sin_addr), ip_addr, INET_ADDRSTRLEN); 

  printf("\n[DY_PROXY_INFO] Binded socket '%d' to the address '%s:%d'", sockfd, ip_addr, port_number);

  return bind_value;
}


int accept(int sockfd, struct sockaddr *address, socklen_t *address_len)
{
  int (*libc_accept)(int, struct sockaddr*, socklen_t*);
  int accept_value;

  *(void **)(&libc_accept) = dlsym(RTLD_NEXT, "accept");
  if(dlerror()) {
    errno = EACCES;
    return -1;
  }

  accept_value = (*libc_accept)(sockfd, address, address_len);

  struct sockaddr_in *theiraddr = (struct sockaddr_in *) address;
  char ip_addr[INET_ADDRSTRLEN];
  short port_number = theiraddr->sin_port;

  inet_ntop(AF_INET, &(theiraddr->sin_addr), ip_addr, INET_ADDRSTRLEN);

  if (accept_value > 0)
  {
    printf("\n[DY_PROXY_INFO] Accepted socket '%d' to the address '%s:%d'", sockfd, ip_addr, port_number);
  }

  return accept_value;
}  



int connect(int sockfd, const struct sockaddr *address, socklen_t address_len)
{
  int (*libc_connect)(int, const struct sockaddr*, socklen_t);
  int connect_value;

  *(void **)(&libc_connect) = dlsym(RTLD_NEXT, "connect");
  if(dlerror()) {
    errno = EACCES;
    return -1;
  }

  connect_value = (*libc_connect)(sockfd, address, address_len);

  struct sockaddr_in *theiraddr = (struct sockaddr_in *) address;
  char ip_addr[INET_ADDRSTRLEN];
  short port_number = theiraddr->sin_port;

  inet_ntop(AF_INET, &(theiraddr->sin_addr), ip_addr, INET_ADDRSTRLEN);

  printf("\n[DY_PROXY_INFO] Connected socket '%d' to the address '%s:%d'", sockfd, ip_addr, port_number);

  return connect_value;
}




int listen(int sockfd, int backlog)
{
  int (*libc_listen)(int, int);
  int listen_value;

  *(void **)(&libc_listen) = dlsym(RTLD_NEXT, "listen");
  if(dlerror()) {
    errno = EACCES;
    return -1;
  }

  listen_value = (*libc_listen)(sockfd, backlog);

  printf("\n[DY_PROXY_INFO] Listen called on socket '%d'", sockfd);

  return listen_value;
}



int shutdown(int sockfd, int how)
{
  int (*libc_shutdown)(int, int);
  int shutdown_value;

  *(void **)(&libc_shutdown) = dlsym(RTLD_NEXT, "shutdown");
  if(dlerror()) {
    errno = EACCES;
    return -1;
  }

  shutdown_value = (*libc_shutdown)(sockfd, how);

  printf("\n[DY_PROXY_INFO] Socket '%d' closed with option '%d'", sockfd, how);

  return shutdown_value;		
}



int setsockopt(int sockfd, int level, int option_name, const void *option_value, socklen_t option_len)
{
  int (*libc_setsockopt)(int, int, int, const void*, socklen_t);
  int setsockopt_value;

  *(void **)(&libc_setsockopt) = dlsym(RTLD_NEXT, "setsockopt");
  if(dlerror()) {
    errno = EACCES;
    return -1;
  }

  setsockopt_value = (*libc_setsockopt)(sockfd, level, option_name, option_value, option_len);

  printf("\n[DY_PROXY_INFO] Setsockopt called on socket '%d' with level:'%d', option_name:'%d', option_value:'%d'", sockfd, level, option_name, (int)option_value);

  return setsockopt_value;
}
