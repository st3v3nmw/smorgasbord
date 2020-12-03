/*
    Sockets Server in Rust
    by P15/1198/2018 (Mwangi Stephen Kioni)
*/

use std::io::prelude::*;
use std::net::TcpListener;

fn main() {
    let listener = TcpListener::bind("127.0.0.1:1024").unwrap();
    
    let mut buffer;
    for stream in listener.incoming() {
        match stream {
            Ok(mut stream) => {
                println!("A connection has been established.");
                
                stream.write(b"Hello, World!\n").ok(); // send "Hello, World!" to the client.

                buffer = [0; 512];
                stream.read(&mut buffer).ok(); // read what the client has sent
                println!("Received: {}", String::from_utf8_lossy(&buffer[..]));
            },
            Err(e) => println!("Err: {}", e)
        }
    }
}
