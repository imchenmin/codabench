#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    const char *output_path = "/app/output/results.txt";
    if (argc > 1) {
        output_path = argv[1];
    }

    FILE *fp = fopen(output_path, "w");
    if (!fp) {
        perror("Unable to open output file");
        return 1;
    }

    fprintf(fp, "MetricValue,42\n");
    fclose(fp);
    printf("Wrote results to %s\n", output_path);
    return 0;
}
