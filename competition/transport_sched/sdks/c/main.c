#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libgen.h>
#include "cJSON.h"

static char* read_all(const char* path) {
    FILE* f = fopen(path, "rb");
    if (!f) return NULL;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
    long n = ftell(f);
    if (n < 0) { fclose(f); return NULL; }
    if (fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }
    char* buf = (char*)malloc((size_t)n + 1);
    if (!buf) { fclose(f); return NULL; }
    size_t r = fread(buf, 1, (size_t)n, f);
    fclose(f);
    if (r != (size_t)n) { free(buf); return NULL; }
    buf[n] = '\0';
    return buf;
}

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: predict <case_dir> <out_file>\n");
        return 1;
    }
    char* case_dir = argv[1];
    char* out_file = argv[2];
    char* case_id = basename(case_dir);

    char path_machines[1024];
    char path_jobs[1024];
    char path_constraints[1024];
    snprintf(path_machines, sizeof(path_machines), "%s/%s", case_dir, "machines.json");
    snprintf(path_jobs, sizeof(path_jobs), "%s/%s", case_dir, "jobs.json");
    snprintf(path_constraints, sizeof(path_constraints), "%s/%s", case_dir, "constraints.json");

    char* m_txt = read_all(path_machines);
    char* j_txt = read_all(path_jobs);
    char* c_txt = read_all(path_constraints);
    if (!m_txt || !j_txt || !c_txt) {
        fprintf(stderr, "Failed to read input JSON files\n");
        free(m_txt); free(j_txt); free(c_txt);
        return 2;
    }

    cJSON* m_json = cJSON_Parse(m_txt);
    cJSON* j_json = cJSON_Parse(j_txt);
    cJSON* c_json = cJSON_Parse(c_txt);
    if (!m_json || !j_json || !c_json) {
        fprintf(stderr, "Failed to parse JSON\n");
        cJSON_Delete(m_json); cJSON_Delete(j_json); cJSON_Delete(c_json);
        free(m_txt); free(j_txt); free(c_txt);
        return 3;
    }

    cJSON* out_root = cJSON_CreateObject();
    cJSON_AddStringToObject(out_root, "case_id", case_id);
    cJSON* out_machines = cJSON_CreateArray();

    cJSON* machines = cJSON_GetObjectItemCaseSensitive(m_json, "machines");
    if (cJSON_IsArray(machines)) {
        cJSON* it = NULL;
        cJSON_ArrayForEach(it, machines) {
            cJSON* mid = cJSON_GetObjectItemCaseSensitive(it, "machine_id");
            if (cJSON_IsString(mid) && (mid->valuestring != NULL)) {
                cJSON* o = cJSON_CreateObject();
                cJSON_AddStringToObject(o, "machine_id", mid->valuestring);
                cJSON_AddItemToObject(o, "timeline", cJSON_CreateArray());
                cJSON_AddItemToArray(out_machines, o);
            }
        }
    }
    cJSON_AddItemToObject(out_root, "machines", out_machines);

    char* out_str = cJSON_Print(out_root);
    FILE* f = fopen(out_file, "w");
    if (!f || !out_str) {
        if (f) fclose(f);
        cJSON_free(out_str);
        cJSON_Delete(out_root);
        cJSON_Delete(m_json); cJSON_Delete(j_json); cJSON_Delete(c_json);
        free(m_txt); free(j_txt); free(c_txt);
        return 4;
    }
    fputs(out_str, f);
    fclose(f);

    cJSON_free(out_str);
    cJSON_Delete(out_root);
    cJSON_Delete(m_json); cJSON_Delete(j_json); cJSON_Delete(c_json);
    free(m_txt); free(j_txt); free(c_txt);
    return 0;
}