/* SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
 * Deckivo local pairing helper. Credentials arrive only on stdin and are
 * written to a private file; never include them in arguments or logs. */
#include <chiaki/regist.h>
#include <chiaki/base64.h>
#include <chiaki/common.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <time.h>

static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t condition = PTHREAD_COND_INITIALIZER;
static int finished = 0, success = 0;
static ChiakiRegisteredHost registered;

static void callback(ChiakiRegistEvent *event, void *user)
{
    (void)user;
    pthread_mutex_lock(&mutex);
    success = event->type == CHIAKI_REGIST_EVENT_TYPE_FINISHED_SUCCESS;
    if (success && event->registered_host) registered = *event->registered_host;
    finished = 1;
    pthread_cond_signal(&condition);
    pthread_mutex_unlock(&mutex);
}

static void hex(FILE *file, const unsigned char *bytes, size_t count)
{
    fputc('"', file);
    for (size_t i = 0; i < count; i++) fprintf(file, "%02x", bytes[i]);
    fputc('"', file);
}

static void string(FILE *file, const char *value, size_t limit)
{
    fputc('"', file);
    for (size_t i = 0; i < limit && value[i]; i++) {
        unsigned char c = (unsigned char)value[i];
        if (c == '"' || c == '\\') fputc('\\', file);
        if (c < 32) fprintf(file, "\\u%04x", c);
        else fputc(c, file);
    }
    fputc('"', file);
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    char host[256], account[64], pin[32];
    if (!fgets(host, sizeof(host), stdin) || !fgets(account, sizeof(account), stdin)
            || !fgets(pin, sizeof(pin), stdin)) return 2;
    host[strcspn(host, "\r\n")] = 0;
    account[strcspn(account, "\r\n")] = 0;
    pin[strcspn(pin, "\r\n")] = 0;
    if (!*host || strlen(pin) != 8 || strspn(pin, "0123456789") != 8) return 2;
    if (chiaki_lib_init() != CHIAKI_ERR_SUCCESS) return 3;
    ChiakiRegistInfo info = {0};
    info.target = CHIAKI_TARGET_PS5_1;
    info.host = host;
    info.broadcast = false;
    info.pin = (uint32_t)strtoul(pin, NULL, 10);
    size_t size = sizeof(info.psn_account_id);
    if (chiaki_base64_decode(account, strlen(account), info.psn_account_id, &size)
            != CHIAKI_ERR_SUCCESS || size != sizeof(info.psn_account_id)) return 2;
    ChiakiLog log;
    chiaki_log_init(&log, 0, NULL, NULL);
    ChiakiRegist registration;
    if (chiaki_regist_start(&registration, &log, &info, callback, NULL)
            != CHIAKI_ERR_SUCCESS) return 3;
    struct timespec deadline;
    clock_gettime(CLOCK_REALTIME, &deadline);
    deadline.tv_sec += 35;
    pthread_mutex_lock(&mutex);
    while (!finished) {
        if (pthread_cond_timedwait(&condition, &mutex, &deadline)) break;
    }
    pthread_mutex_unlock(&mutex);
    chiaki_regist_stop(&registration);
    chiaki_regist_fini(&registration);
    memset(pin, 0, sizeof(pin));
    memset(account, 0, sizeof(account));
    if (!finished || !success) { fputs("Pairing failed or timed out.\n", stderr); return 4; }
    int descriptor = open(argv[1], O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW, 0600);
    if (descriptor < 0) return 5;
    if (fchmod(descriptor, 0600)) { close(descriptor); return 5; }
    FILE *file = fdopen(descriptor, "w");
    if (!file) { close(descriptor); return 5; }
    fprintf(file, "{\"target\":%d,\"server_nickname\":", registered.target);
    string(file, registered.server_nickname, sizeof(registered.server_nickname));
    fputs(",\"server_mac\":", file); hex(file, registered.server_mac, 6);
    fputs(",\"rp_regist_key\":", file);
    hex(file, (const unsigned char *)registered.rp_regist_key, sizeof(registered.rp_regist_key));
    fprintf(file, ",\"rp_key_type\":%u,\"rp_key\":", registered.rp_key_type);
    hex(file, registered.rp_key, sizeof(registered.rp_key));
    fputs("}\n", file);
    int error = fflush(file) || fsync(descriptor);
    error |= fclose(file) != 0;
    memset(&registered, 0, sizeof(registered));
    return error ? 5 : 0;
}
