#include <iostream>
#include <filesystem>
#include <fstream>
#include <string>
#include "json.hpp"
namespace fs = std::filesystem;

static double jgetd(const nlohmann::json& j, const std::string& k, double defv) {
    if (j.contains(k) && j[k].is_number()) return j[k].get<double>();
    return defv;
}

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: predict <case_dir> <out_file>\n";
        return 1;
    }
    std::string case_dir = argv[1];
    std::string out_file = argv[2];
    std::string case_id = fs::path(case_dir).filename().string();

    std::ifstream mifs(fs::path(case_dir) / "machine.json");
    std::ifstream jifs(fs::path(case_dir) / "job.json");
    nlohmann::json machine = nlohmann::json::parse(mifs);
    nlohmann::json job = nlohmann::json::parse(jifs);

    double atm_pick = jgetd(machine["EFEM"]["AtmRobot"], "pick", 0.0);
    double atm_place = jgetd(machine["EFEM"]["AtmRobot"], "place", 0.0);
    double vac_pick = jgetd(machine["TM1"]["VacRobot"], "pick", 0.0);
    double vac_place = jgetd(machine["TM1"]["VacRobot"], "place", 0.0);
    double ll1_vent = jgetd(machine["LoadLock1"], "vent", 0.0);

    nlohmann::json out;
    out["AtmRobot-1"] = nlohmann::json::array();
    out["LoadLock1-1"] = nlohmann::json::array();
    out["TM1-VacRobot-1"] = nlohmann::json::array();
    out["PM1"] = nlohmann::json::array();
    out["LoadLock2-1"] = nlohmann::json::array();

    double avail_atm = 0.0, avail_ll1 = 0.0, avail_vac = 0.0, avail_pm1 = 0.0, avail_ll2 = 0.0;

    for (auto& lot : job["Lot"]) {
        double start = jgetd(lot, "StartTime", 0.0);
        int lot_id = (int)jgetd(lot, "Id", 0.0);
        double min_proc = 180.0;
        if (lot.contains("Sequence") && lot["Sequence"].is_array()) {
            auto first_pm = lot["Sequence"][1];
            if (first_pm.is_array()) {
                for (auto& d : first_pm) {
                    if (d.contains("PM1") && d["PM1"].is_number()) { min_proc = d["PM1"].get<double>(); break; }
                }
            }
        }
        double t = start;
        for (auto& wv : lot["Wafer"]) {
            int w = wv.get<int>();
            std::string label = "W" + std::to_string(lot_id) + "-" + std::to_string(w);

            double s1 = std::max(t, avail_atm);
            out["AtmRobot-1"].push_back({{"Wafer", label}, {"StartTime", s1}, {"Action", "Pick"}, {"Duration", atm_pick}});
            out["AtmRobot-1"].push_back({{"Wafer", label}, {"StartTime", s1 + atm_pick}, {"Action", "Place"}, {"Duration", atm_place}});
            double end1 = s1 + atm_pick + atm_place;
            avail_atm = end1;

            double s2 = std::max(end1, avail_ll1);
            out["LoadLock1-1"].push_back({{"StartTime", s2}, {"Action", "Vent"}, {"Duration", ll1_vent}});
            double end2 = s2 + ll1_vent;
            avail_ll1 = end2;

            double s3 = std::max(end2, avail_vac);
            out["TM1-VacRobot-1"].push_back({{"Wafer", label}, {"StartTime", s3}, {"Action", "Pick"}, {"Duration", vac_pick}});
            out["TM1-VacRobot-1"].push_back({{"Wafer", label}, {"StartTime", s3 + vac_pick}, {"Action", "Place"}, {"Duration", vac_place}});
            double end3 = s3 + vac_pick + vac_place;
            avail_vac = end3;

            double s4 = std::max(end3, avail_pm1);
            out["PM1"].push_back({{"Wafer", label}, {"StartTime", s4}, {"Action", "Execute"}, {"Duration", min_proc}});
            double end4 = s4 + min_proc;
            avail_pm1 = end4;

            double s5 = std::max(end4, avail_ll2);
            out["LoadLock2-1"].push_back({{"Wafer", label}, {"StartTime", s5}, {"Action", "Place"}, {"Duration", atm_place}});
            double end5 = s5 + atm_place;
            avail_ll2 = end5;

            t = end5 + 10.0;
        }
    }

    std::ofstream ofs(out_file);
    ofs << out.dump(2) << std::endl;
    return 0;
}
