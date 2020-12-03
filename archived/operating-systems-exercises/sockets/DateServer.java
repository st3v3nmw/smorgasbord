import java.net.*;
import java.io.*;
import java.util.Date;

public class DateServer {
    public static void main(String[] args) {
        try {
            ServerSocket sock = new ServerSocket(6013);
            while (true) {
                Socket client = sock.accept();
                InputStream in = client.getInputStream();
                BufferedReader bin = new BufferedReader(new InputStreamReader(in));
                String clientName = bin.readLine();

                PrintWriter pout = new PrintWriter(client.getOutputStream(), true);
                Date currentDate = new Date();
                pout.println(currentDate.toString());
                System.out.println(clientName + " connected at " + currentDate.toString());
                client.close();
            }
        } catch (IOException e) {
            System.err.println(e);
        }
    }
}