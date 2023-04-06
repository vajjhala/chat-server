

The entire code is written in Python3.6. Please use this to thest both the 
server and the client. 

For each part these are the two programs and their usage:
```
$ python3 user.py -h
usage: user.py [-h] [-s HOST] [-p PORT]

optional arguments:
  -h, --help  show this help message and exit
  -s HOST     specify remote server name or ip-address
  -p PORT     specify port number
  
$ python3 server.py -h
usage: server.py [-h] [-p PORT] [-c CLIENTS]

optional arguments:
  -h, --help  show this help message and exit
  -p PORT     specify port number
  -c CLIENTS  maximum number of clients

```
The sever uses multithreading with each thread given to a seperate user.
The client uses two threads to handle receiving and sending seperated, with 
synchronisation taken care by a global lock.


Note-1:

I have made a few minor changes to the protocol messgaes, I had to make these 
changes to account for Python multi-threading, which does not include synchronization
(like Java) and this had to be implemented using Locks:

For example: Each protocol message ends with a semi-colon, this is used to seperate 
the messages recieved by the client-buffer.
 
For this reason I would recommend my server and client against each other and 
not with some other Java code because this will break compatability.

Note-2:
```
 << is the input prompt
 >> is the output prompt
```
See example below.
Sometimes a received message might be in the buffer and could take a few 
prompts before it is posted. For this reason press enter(return) key a few times 
at the input-prompt and the received message will be printed.
This is essentially done to release the lock from input-prompt to the output
prompt and go over the received-messages from the received-message-buffer.
 


Example of three clients and one server.
I have used the default argumenst here. Ideally one much provide the 
arguments. Otherwise the host will default to localhost, and port to 58732.

```    
    SERVER:
        $ python3 server.py 
        Social App running on HOSTNAME - v-76 

        vajj joined
        raj joined
        raj and vajj are now friends
        vajj posted: #status Jackson
        shant joined
        shant posted: #status Me

    CLIENT-1
        $ python3 user.py 
        Enter username: raj
        >>'raj' connected to server on ('v-76', 58732)
        << 
        <<
        >>received friend request from vajj: type '@friend vajj' to accept  OR 
        type '@deny vajj' to reject
        <<@friend vajj
        <<
        >>raj and vajj are now friends
        <<@add chelsea vajj
        <<
        <<
        <<
        >>vajj is now in group chelsea
        >>new status from 'vajj'': Jackson
        <<
        <<
        >>new user 'shant' has joined the app
        <<
        >>received friend request from shant: type '@friend shant' to accept  
        OR type '@deny shant' to reject
        <<

    CLIENT-2
        $ python3 user.py 
        Enter username: shant
        <<
        >>'shant' connected to server on ('v-76', 58732)
        <<@connect raj
        <<#status Me
        <<
        <<
        >>#statusPosted

    CLIENT-3

        $ python3 user.py 
        Enter username: vajj
        >>'vajj' connected to server on ('v-76', 58732)
        <<           
        >>new user 'raj' has joined the app
        <<@connect raj
        <<
        >>raj and vajj are now friends
        >>vajj is now in group chelsea
        <<#status Jackson
        <<
        >>#statusPosted
```

