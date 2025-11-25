#include <iostream>
#include <filesystem>
#include <fstream>
#include <string>
#include "json.hpp"
namespace fs = std::filesystem;

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: predict <case_dir> <out_file>\n";
        return 1;
    }
    std::string case_dir = argv[1];
    std::string out_file = argv[2];
    std::string case_id = fs::path(case_dir).filename().string();

    std::ifstream mifs(fs::path(case_dir) / "machines.json");
    std::ifstream jifs(fs::path(case_dir) / "jobs.json");
    std::ifstream cifs(fs::path(case_dir) / "constraints.json");
    if (!mifs || !jifs || !cifs) {
        std::cerr << "Failed to read input JSON files\n";
        return 2;
    }
    nlohmann::json mjson = nlohmann::json::parse(mifs);
    nlohmann::json jjson = nlohmann::json::parse(jifs);
    nlohmann::json cjson = nlohmann::json::parse(cifs);

    nlohmann::json out;
    out["case_id"] = case_id;
    out["machines"] = nlohmann::json::array();
    if (mjson.contains("machines") && mjson["machines"].is_array()) {
        for (auto& m : mjson["machines"]) {
            if (m.contains("machine_id") && m["machine_id"].is_string()) {
                nlohmann::json o;
                o["machine_id"] = m["machine_id"].get<std::string>();
                o["timeline"] = nlohmann::json::array();
                out["machines"].push_back(o);
            }
        }
    }
    std::ofstream ofs(out_file);
    ofs << out.dump(2) << std::endl;
    return 0;
}