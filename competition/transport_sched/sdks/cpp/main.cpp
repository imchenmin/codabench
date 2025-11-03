#include <iostream>
#include <filesystem>
#include <fstream>
namespace fs = std::filesystem;

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: predict <case_dir> <out_file>\n";
        return 1;
    }
    std::string case_dir = argv[1];
    std::string out_file = argv[2];
    std::string case_id = fs::path(case_dir).filename().string();
    std::ofstream ofs(out_file);
    ofs << "{\n  \"case_id\": \"" << case_id << "\",\n  \"machines\": []\n}\n";
    return 0;
}