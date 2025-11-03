import java.io.*;
import java.nio.file.*;

public class Main {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: java Main <case_dir> <out_file>");
            System.exit(1);
        }
        String caseDir = args[0];
        String outFile = args[1];
        String caseId = Paths.get(caseDir).getFileName().toString();
        String json = String.format("{\n  \"case_id\": \"%s\",\n  \"machines\": []\n}\n", caseId);
        Path out = Paths.get(outFile);
        Files.createDirectories(out.getParent());
        Files.write(out, json.getBytes("UTF-8"));
    }
}