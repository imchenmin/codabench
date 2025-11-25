import java.io.*;
import java.nio.file.*;
import com.google.gson.*;

public class Main {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: java Main <case_dir> <out_file>");
            System.exit(1);
        }
        String caseDir = args[0];
        String outFile = args[1];
        String caseId = Paths.get(caseDir).getFileName().toString();

        Gson gson = new Gson();
        Reader mReader = Files.newBufferedReader(Paths.get(caseDir, "machines.json"));
        Reader jReader = Files.newBufferedReader(Paths.get(caseDir, "jobs.json"));
        Reader cReader = Files.newBufferedReader(Paths.get(caseDir, "constraints.json"));
        JsonObject mjson = gson.fromJson(mReader, JsonObject.class);
        JsonObject jjson = gson.fromJson(jReader, JsonObject.class);
        JsonObject cjson = gson.fromJson(cReader, JsonObject.class);
        mReader.close();
        jReader.close();
        cReader.close();

        JsonObject out = new JsonObject();
        out.addProperty("case_id", caseId);
        JsonArray outMachines = new JsonArray();
        JsonArray machines = mjson.getAsJsonArray("machines");
        if (machines != null) {
            for (JsonElement el : machines) {
                JsonObject m = el.getAsJsonObject();
                if (m.has("machine_id")) {
                    JsonObject o = new JsonObject();
                    o.addProperty("machine_id", m.get("machine_id").getAsString());
                    o.add("timeline", new JsonArray());
                    outMachines.add(o);
                }
            }
        }
        out.add("machines", outMachines);

        Path outPath = Paths.get(outFile);
        Files.createDirectories(outPath.getParent());
        try (Writer w = Files.newBufferedWriter(outPath)) {
            w.write(new GsonBuilder().setPrettyPrinting().create().toJson(out));
        }
    }
}