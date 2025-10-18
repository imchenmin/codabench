import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;

public class Main {
    public static void main(String[] args) throws IOException {
        if (args.length < 2) {
            System.err.println("Usage: java Main <input.csv> <output.csv>");
            System.exit(1);
        }
        String inputPath = args[0];
        String outputPath = args[1];

        try (BufferedReader reader = new BufferedReader(new FileReader(inputPath));
             FileWriter writer = new FileWriter(outputPath)) {
            writer.write("id,sum\n");
            String line = reader.readLine(); // header
            if (line == null) {
                throw new IOException("Empty input file");
            }
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                if (parts.length != 3) {
                    throw new IOException("Invalid row: " + line);
                }
                int id = Integer.parseInt(parts[0]);
                long a = Long.parseLong(parts[1]);
                long b = Long.parseLong(parts[2]);
                long sum = a + b;
                writer.write(id + "," + sum + "\n");
            }
        }
    }
}
