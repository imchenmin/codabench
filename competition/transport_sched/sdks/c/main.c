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

static double get_double(cJSON* obj, const char* key, double defv) {
    cJSON* v = cJSON_GetObjectItemCaseSensitive(obj, key);
    if (cJSON_IsNumber(v)) return v->valuedouble;
    return defv;
}

static cJSON* append_evt_with_wafer(cJSON* arr, const char* wafer, double start, const char* action, double dur) {
    cJSON* e = cJSON_CreateObject();
    cJSON_AddStringToObject(e, "Wafer", wafer);
    cJSON_AddNumberToObject(e, "StartTime", start);
    cJSON_AddStringToObject(e, "Action", action);
    cJSON_AddNumberToObject(e, "Duration", dur);
    cJSON_AddItemToArray(arr, e);
    return e;
}

static cJSON* append_evt_no_wafer(cJSON* arr, double start, const char* action, double dur) {
    cJSON* e = cJSON_CreateObject();
    cJSON_AddNumberToObject(e, "StartTime", start);
    cJSON_AddStringToObject(e, "Action", action);
    cJSON_AddNumberToObject(e, "Duration", dur);
    cJSON_AddItemToArray(arr, e);
    return e;
}

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: predict <case_dir> <out_file>\n");
        return 1;
    }
    char* case_dir = argv[1];
    char* out_file = argv[2];
    char* case_id = basename(case_dir);

    char path_machine[1024];
    char path_job[1024];
    char path_am[1024];
    snprintf(path_machine, sizeof(path_machine), "%s/%s", case_dir, "machine.json");
    snprintf(path_job, sizeof(path_job), "%s/%s", case_dir, "job.json");
    snprintf(path_am, sizeof(path_am), "%s/%s", case_dir, "am.json");

    char* m_txt = read_all(path_machine);
    char* j_txt = read_all(path_job);
    char* a_txt = read_all(path_am);
    if (!m_txt || !j_txt) {
        fprintf(stderr, "Failed to read input JSON files\n");
        free(m_txt); free(j_txt); free(a_txt);
        return 2;
    }

    cJSON* machine = cJSON_Parse(m_txt);
    cJSON* job = cJSON_Parse(j_txt);
    cJSON* am = a_txt ? cJSON_Parse(a_txt) : NULL;
    if (!machine || !job) {
        fprintf(stderr, "Failed to parse JSON\n");
        cJSON_Delete(machine); cJSON_Delete(job); cJSON_Delete(am);
        free(m_txt); free(j_txt); free(a_txt);
        return 3;
    }

    cJSON* efem = cJSON_GetObjectItemCaseSensitive(machine, "EFEM");
    cJSON* atm = efem ? cJSON_GetObjectItemCaseSensitive(efem, "AtmRobot") : NULL;
    double atm_pick = atm ? get_double(atm, "pick", 0.0) : 0.0;
    double atm_place = atm ? get_double(atm, "place", 0.0) : 0.0;

    cJSON* tm1 = cJSON_GetObjectItemCaseSensitive(machine, "TM1");
    cJSON* vac = tm1 ? cJSON_GetObjectItemCaseSensitive(tm1, "VacRobot") : NULL;
    double vac_pick = vac ? get_double(vac, "pick", 0.0) : 0.0;
    double vac_place = vac ? get_double(vac, "place", 0.0) : 0.0;

    cJSON* ll1 = cJSON_GetObjectItemCaseSensitive(machine, "LoadLock1");
    double ll1_pump = ll1 ? get_double(ll1, "pump", 0.0) : 0.0;
    double ll1_vent = ll1 ? get_double(ll1, "vent", 0.0) : 0.0;

    cJSON* out_root = cJSON_CreateObject();
    cJSON* arr_atm = cJSON_CreateArray();
    cJSON* arr_ll1 = cJSON_CreateArray();
    cJSON* arr_vac = cJSON_CreateArray();
    cJSON* arr_pm1 = cJSON_CreateArray();
    cJSON* arr_ll2 = cJSON_CreateArray();
    cJSON_AddItemToObject(out_root, "AtmRobot-1", arr_atm);
    cJSON_AddItemToObject(out_root, "LoadLock1-1", arr_ll1);
    cJSON_AddItemToObject(out_root, "TM1-VacRobot-1", arr_vac);
    cJSON_AddItemToObject(out_root, "PM1", arr_pm1);
    cJSON_AddItemToObject(out_root, "LoadLock2-1", arr_ll2);

    double avail_atm = 0.0, avail_ll1 = 0.0, avail_vac = 0.0, avail_pm1 = 0.0, avail_ll2 = 0.0;

    cJSON* lots = cJSON_GetObjectItemCaseSensitive(job, "Lot");
    if (cJSON_IsArray(lots)) {
        cJSON* lot = NULL;
        cJSON_ArrayForEach(lot, lots) {
            double start = get_double(lot, "StartTime", 0.0);
            int lot_id = (int)get_double(lot, "Id", 0);
            cJSON* wafers = cJSON_GetObjectItemCaseSensitive(lot, "Wafer");
            cJSON* seq = cJSON_GetObjectItemCaseSensitive(lot, "Sequence");
            double min_proc = 180.0;
            if (cJSON_IsArray(seq)) {
                cJSON* first_pm = cJSON_GetArrayItem(seq, 1);
                if (cJSON_IsArray(first_pm)) {
                    int n = cJSON_GetArraySize(first_pm);
                    for (int i = 0; i < n; ++i) {
                        cJSON* d = cJSON_GetArrayItem(first_pm, i);
                        if (cJSON_IsObject(d)) {
                            cJSON* v = cJSON_GetObjectItemCaseSensitive(d, "PM1");
                            if (cJSON_IsNumber(v)) { min_proc = v->valuedouble; break; }
                        }
                    }
                }
            }
            double t = start;
            if (cJSON_IsArray(wafers)) {
                int n = cJSON_GetArraySize(wafers);
                for (int i = 0; i < n; ++i) {
                    int w = (int)cJSON_GetArrayItem(wafers, i)->valuedouble;
                    char label[64];
                    snprintf(label, sizeof(label), "W%d-%d", lot_id, w);

                    double s1 = t > avail_atm ? t : avail_atm;
                    append_evt_with_wafer(arr_atm, label, s1, "Pick", atm_pick);
                    append_evt_with_wafer(arr_atm, label, s1 + atm_pick, "Place", atm_place);
                    double end1 = s1 + atm_pick + atm_place;
                    avail_atm = end1;

                    double s2 = end1 > avail_ll1 ? end1 : avail_ll1;
                    append_evt_no_wafer(arr_ll1, s2, "Vent", ll1_vent);
                    double end2 = s2 + ll1_vent;
                    avail_ll1 = end2;

                    double s3 = end2 > avail_vac ? end2 : avail_vac;
                    append_evt_with_wafer(arr_vac, label, s3, "Pick", vac_pick);
                    append_evt_with_wafer(arr_vac, label, s3 + vac_pick, "Place", vac_place);
                    double end3 = s3 + vac_pick + vac_place;
                    avail_vac = end3;

                    double s4 = end3 > avail_pm1 ? end3 : avail_pm1;
                    append_evt_with_wafer(arr_pm1, label, s4, "Execute", min_proc);
                    double end4 = s4 + min_proc;
                    avail_pm1 = end4;

                    double s5 = end4 > avail_ll2 ? end4 : avail_ll2;
                    append_evt_with_wafer(arr_ll2, label, s5, "Place", atm_place);
                    double end5 = s5 + atm_place;
                    avail_ll2 = end5;

                    t = end5 + 10.0;
                }
            }
        }
    }

    FILE* f = fopen(out_file, "w");
    if (!f) {
        cJSON_Delete(machine); cJSON_Delete(job); cJSON_Delete(am);
        free(m_txt); free(j_txt); free(a_txt);
        return 4;
    }
    char* out_str = cJSON_Print(out_root);
    fputs(out_str, f);
    fclose(f);
    cJSON_free(out_str);

    cJSON_Delete(out_root);
    cJSON_Delete(machine); cJSON_Delete(job); cJSON_Delete(am);
    free(m_txt); free(j_txt); free(a_txt);
    return 0;
}
