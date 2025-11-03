#include <stdio.h>
#include <string.h>
#include <libgen.h>

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: predict <case_dir> <out_file>\n");
        return 1;
    }
    char* case_dir = argv[1];
    char* out_file = argv[2];
    char* base = basename(case_dir);
    FILE* f = fopen(out_file, "w");
    if (!f) return 2;
    fprintf(f, "{\n  \"case_id\": \"%s\",\n  \"machines\": []\n}\n", base);
    fclose(f);
    return 0;
}