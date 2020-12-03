/*
    Sockets Client in Rust
    by P15/1198/2018 (Mwangi Stephen Kioni)
*/

use std::io::prelude::*;
use std::net::TcpStream;

fn main() {
    let stream = TcpStream::connect("127.0.0.1:1024");
    match stream {
        Ok(mut stream) => {
            println!("Connected to the server.");

            stream.write(b"Hey, you!\n").ok(); // send "Hey, you!" to the server.
            
            let mut buffer = [0; 512];
            stream.read(&mut buffer).ok(); // read what the server has sent
            println!("Received: {}", String::from_utf8_lossy(&buffer[..]));
        },
        Err(e) => println!("Err: {}", e)
    }
}