import java.io.FileWriter;
import java.io.IOException;

public class Main {
    public static void main(String[] args) throws IOException {
        String outputPath = "/app/output/results.txt";
        if (args.length > 0) {
            outputPath = args[0];
        }
        try (FileWriter writer = new FileWriter(outputPath)) {
            writer.write("MetricValue,7\n");
        }
        System.out.println("Wrote results to " + outputPath);
    }
}
