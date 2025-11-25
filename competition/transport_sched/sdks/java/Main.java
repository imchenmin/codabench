import java.io.*;
import java.nio.file.*;
import java.util.*;
import com.google.gson.*;

public class Main {
    static double jgetd(JsonObject obj, String key, double defv) {
        if (obj == null) return defv;
        JsonElement el = obj.get(key);
        return (el != null && el.isJsonPrimitive() && ((JsonPrimitive) el).isNumber()) ? el.getAsDouble() : defv;
    }

    static JsonObject evtWithWafer(String wafer, double start, String action, double dur) {
        JsonObject e = new JsonObject();
        e.addProperty("Wafer", wafer);
        e.addProperty("StartTime", start);
        e.addProperty("Action", action);
        e.addProperty("Duration", dur);
        return e;
    }

    static JsonObject evtNoWafer(double start, String action, double dur) {
        JsonObject e = new JsonObject();
        e.addProperty("StartTime", start);
        e.addProperty("Action", action);
        e.addProperty("Duration", dur);
        return e;
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: java Main <case_dir> <out_file>");
            System.exit(1);
        }
        String caseDir = args[0];
        String outFile = args[1];

        Gson gson = new Gson();
        JsonObject machine;
        JsonObject job;
        try (Reader mReader = Files.newBufferedReader(Paths.get(caseDir, "machine.json"));
             Reader jReader = Files.newBufferedReader(Paths.get(caseDir, "job.json"))) {
            machine = gson.fromJson(mReader, JsonObject.class);
            job = gson.fromJson(jReader, JsonObject.class);
        }
        JsonObject efem = machine.getAsJsonObject("EFEM");
        JsonObject atm = efem != null ? efem.getAsJsonObject("AtmRobot") : null;
        double atmPick = jgetd(atm, "pick", 0.0);
        double atmPlace = jgetd(atm, "place", 0.0);
        JsonObject tm1 = machine.getAsJsonObject("TM1");
        JsonObject vac = tm1 != null ? tm1.getAsJsonObject("VacRobot") : null;
        double vacPick = jgetd(vac, "pick", 0.0);
        double vacPlace = jgetd(vac, "place", 0.0);
        JsonObject ll1 = machine.getAsJsonObject("LoadLock1");
        double ll1Vent = jgetd(ll1, "vent", 0.0);

        JsonArray atmArr = new JsonArray();
        JsonArray ll1Arr = new JsonArray();
        JsonArray vacArr = new JsonArray();
        JsonArray pm1Arr = new JsonArray();
        JsonArray ll2Arr = new JsonArray();

        double availAtm = 0.0, availLl1 = 0.0, availVac = 0.0, availPm1 = 0.0, availLl2 = 0.0;

        JsonArray lots = job.getAsJsonArray("Lot");
        if (lots != null) {
            for (JsonElement lotEl : lots) {
                JsonObject lot = lotEl.getAsJsonObject();
                double start = jgetd(lot, "StartTime", 0.0);
                int lotId = lot.get("Id").getAsInt();
                double minProc = 180.0;
                JsonArray seq = lot.getAsJsonArray("Sequence");
                if (seq != null && seq.size() >= 2) {
                    JsonArray firstPm = seq.get(1).getAsJsonArray();
                    for (JsonElement dEl : firstPm) {
                        JsonObject d = dEl.getAsJsonObject();
                        if (d.has("PM1") && d.get("PM1").isJsonPrimitive()) { minProc = d.get("PM1").getAsDouble(); break; }
                    }
                }
                double t = start;
                JsonArray wafers = lot.getAsJsonArray("Wafer");
                if (wafers != null) {
                    for (JsonElement wEl : wafers) {
                        int w = wEl.getAsInt();
                        String label = "W" + lotId + "-" + w;

                        double s1 = Math.max(t, availAtm);
                        atmArr.add(evtWithWafer(label, s1, "Pick", atmPick));
                        atmArr.add(evtWithWafer(label, s1 + atmPick, "Place", atmPlace));
                        double end1 = s1 + atmPick + atmPlace;
                        availAtm = end1;

                        double s2 = Math.max(end1, availLl1);
                        ll1Arr.add(evtNoWafer(s2, "Vent", ll1Vent));
                        double end2 = s2 + ll1Vent;
                        availLl1 = end2;

                        double s3 = Math.max(end2, availVac);
                        vacArr.add(evtWithWafer(label, s3, "Pick", vacPick));
                        vacArr.add(evtWithWafer(label, s3 + vacPick, "Place", vacPlace));
                        double end3 = s3 + vacPick + vacPlace;
                        availVac = end3;

                        double s4 = Math.max(end3, availPm1);
                        pm1Arr.add(evtWithWafer(label, s4, "Execute", minProc));
                        double end4 = s4 + minProc;
                        availPm1 = end4;

                        double s5 = Math.max(end4, availLl2);
                        ll2Arr.add(evtWithWafer(label, s5, "Place", atmPlace));
                        double end5 = s5 + atmPlace;
                        availLl2 = end5;

                        t = end5 + 10.0;
                    }
                }
            }
        }

        JsonObject out = new JsonObject();
        out.add("AtmRobot-1", atmArr);
        out.add("LoadLock1-1", ll1Arr);
        out.add("TM1-VacRobot-1", vacArr);
        out.add("PM1", pm1Arr);
        out.add("LoadLock2-1", ll2Arr);

        Path outPath = Paths.get(outFile);
        Files.createDirectories(outPath.getParent());
        try (Writer w = Files.newBufferedWriter(outPath)) {
            w.write(new GsonBuilder().setPrettyPrinting().create().toJson(out));
        }
    }
}
