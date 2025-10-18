#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char **argv) {
    std::string output_path = "/app/output/results.txt";
    if (argc > 1) {
        output_path = argv[1];
    }

    std::ofstream out(output_path);
    if (!out.is_open()) {
        std::cerr << "Failed to open output file: " << output_path << std::endl;
        return 1;
    }

    out << "MetricValue,3.14" << std::endl;
    out.close();
    std::cout << "Wrote results to " << output_path << std::endl;
    return 0;
}
