/* SPDX-License-Identifier: GPL-3.0-or-later
 * RemTeh Pair Helper 0.1.0. Local, short-lived, read-only account pairing helper.
 * Registry key numbers/formula from ps5-payload-dev/linkdev, regmgr.h,
 * Copyright (C) 2024 John Tornblom, GPL-3.0-or-later, commit
 * 8b1d47ed3acb5ead61602708ac1e58ad43f066f6.
 * No registry writes, kernel patches, Remote Play PIN generation or save access.
 */
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

#define PORT 38080
#define TTL_SECONDS 300
#define MAX_ATTEMPTS 5
#define REQUEST_LIMIT 2048

#ifndef HOST_TEST
int sceUserServiceGetForegroundUser(int *);
int sceRegMgrGetInt(long, int *);
int sceRegMgrGetBin(long, void *, int);
typedef struct { char reserved[45]; char message[3075]; } notification_t;
int sceKernelSendNotificationRequest(int, notification_t *, size_t, int);
#endif

static void notify(const char *message) {
#ifdef HOST_TEST
    (void)message; /* Never log pairing codes or account identifiers. */
#else
    notification_t request = {0};
    snprintf(request.message, sizeof request.message, "%s", message);
    sceKernelSendNotificationRequest(0, &request, sizeof request, 0);
#endif
}

static int active_account(int *user, uint8_t account[8]) {
#ifdef HOST_TEST
    *user = 7;
    for (int i = 0; i < 8; ++i) account[i] = (uint8_t)(i + 1);
    return 0;
#else
    if (sceUserServiceGetForegroundUser(user) != 0) return -1;
    for (int slot = 1; slot <= 16; ++slot) {
        int candidate = -1;
        const long offset = (slot - 1) * 65536L;
        if (sceRegMgrGetInt(125829376L + offset, &candidate) != 0) continue;
        if (candidate != *user) continue;
        if (sceRegMgrGetBin(125830400L + offset, account, 8) != 0) return -1;
        uint8_t zero = 0, ones = 0;
        for (int i = 0; i < 8; ++i) { zero |= account[i]; ones |= account[i] ^ 255; }
        return zero && ones ? 0 : -1;
    }
    return -1;
#endif
}

static void base64_account(const uint8_t in[8], char out[13]) {
    const char *alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    size_t pos = 0;
    for (size_t i = 0; i < 8; i += 3) {
        const uint32_t n = ((uint32_t)in[i] << 16) |
            ((uint32_t)(i + 1 < 8 ? in[i + 1] : 0) << 8) |
            (i + 2 < 8 ? in[i + 2] : 0);
        out[pos++] = alphabet[(n >> 18) & 63];
        out[pos++] = alphabet[(n >> 12) & 63];
        out[pos++] = i + 1 < 8 ? alphabet[(n >> 6) & 63] : '=';
        out[pos++] = i + 2 < 8 ? alphabet[n & 63] : '=';
    }
    out[pos] = '\0';
}

static int64_t now_ms(void) {
    struct timespec value;
    clock_gettime(CLOCK_MONOTONIC, &value);
    return (int64_t)value.tv_sec * 1000 + value.tv_nsec / 1000000;
}

static bool permitted_peer(const struct sockaddr_in *peer) {
    uint32_t ip = ntohl(peer->sin_addr.s_addr);
#ifdef HOST_TEST
    if ((ip >> 24) == 127) return true;
#endif
    return (ip >> 24) == 10 || (ip >> 20) == 0xAC1 || (ip >> 16) == 0xC0A8;
}

static bool send_all(int fd, const char *data, size_t length) {
    while (length) {
        ssize_t n = send(fd, data, length, 0);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return false;
        data += n; length -= (size_t)n;
    }
    return true;
}

static bool reply(int fd, int status, const char *body) {
    char header[512];
    int count = snprintf(header, sizeof header,
        "HTTP/1.1 %d Response\r\nContent-Type: application/json\r\n"
        "Content-Length: %zu\r\nCache-Control: no-store\r\n"
        "X-Content-Type-Options: nosniff\r\nConnection: close\r\n\r\n", status, strlen(body));
    return send_all(fd, header, (size_t)count) && send_all(fd, body, strlen(body));
}

/* -1 bad request, 0 status only, 1 pairing request. Exact, bounded HTTP parser. */
static int read_request(int fd, char body[9], int64_t session_deadline) {
    char data[REQUEST_LIMIT + 1];
    size_t used = 0, header_size = 0;
    int64_t deadline = now_ms() + 2000;
    if (deadline > session_deadline) deadline = session_deadline;
    while (used < REQUEST_LIMIT && now_ms() < deadline) {
        struct pollfd pollfd = { .fd = fd, .events = POLLIN };
        int remaining = (int)(deadline - now_ms());
        if (remaining <= 0 || poll(&pollfd, 1, remaining) <= 0) return -1;
        ssize_t n = recv(fd, data + used, REQUEST_LIMIT - used, 0);
        if (n <= 0) return -1;
        used += (size_t)n; data[used] = 0;
        if (memchr(data, 0, used)) return -1;
        if (!header_size) {
            char *end = strstr(data, "\r\n\r\n");
            if (!end) continue;
            header_size = (size_t)(end - data) + 4;
            if (strncmp(data, "GET /v1/status HTTP/1.1\r\n", 25) == 0) return 0;
            if (strncmp(data, "POST /v1/account HTTP/1.1\r\n", 27) != 0) return -1;
            bool client = false, length = false, content_type = false;
            char header[REQUEST_LIMIT + 1];
            memcpy(header, data, header_size); header[header_size] = 0;
            char *save = NULL;
            for (char *line = strtok_r(header, "\r\n", &save); line; line = strtok_r(NULL, "\r\n", &save)) {
                if (!strncasecmp(line, "Origin:", 7) || !strncasecmp(line, "Transfer-Encoding:", 18)) return -1;
                if (!strncasecmp(line, "Content-Length:", 15)) {
                    if (length || strcmp(line + 15, " 8") != 0) return -1;
                    length = true;
                }
                if (!strcasecmp(line, "X-RemTeh-Client: 1")) client = true;
                if (!strcasecmp(line, "Content-Type: text/plain")) content_type = true;
            }
            if (!client || !length || !content_type) return -1;
        }
        if (used >= header_size + 8) {
            if (used != header_size + 8) return -1;
            memcpy(body, data + header_size, 8); body[8] = 0;
            for (int i = 0; i < 8; ++i) if (body[i] < '0' || body[i] > '9') return -1;
            return 1;
        }
    }
    return -1;
}

int main(void) {
    signal(SIGPIPE, SIG_IGN);
    int user;
    uint8_t account[8];
    if (active_account(&user, account)) {
        notify("RemTeh: cannot read active profile Account ID. Sign in to your local PS5 profile. No settings changed.");
        return 1;
    }
    int port = PORT, ttl = TTL_SECONDS;
    char code[9];
#ifdef HOST_TEST
    memcpy(code, "12345678", 9);
    if (getenv("REMTEH_TEST_PORT")) port = atoi(getenv("REMTEH_TEST_PORT"));
    if (getenv("REMTEH_TEST_TTL")) ttl = atoi(getenv("REMTEH_TEST_TTL"));
#else
    snprintf(code, sizeof code, "%08u", arc4random_uniform(100000000));
#endif
    int server = socket(AF_INET, SOCK_STREAM, 0);
    if (server < 0) return 1;
    int one = 1;
    setsockopt(server, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
    struct sockaddr_in address = { .sin_family = AF_INET, .sin_port = htons((uint16_t)port) };
#ifdef HOST_TEST
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
#else
    address.sin_addr.s_addr = htonl(INADDR_ANY);
#endif
    if (bind(server, (struct sockaddr *)&address, sizeof address) || listen(server, 4)) {
        notify("RemTeh Pair Helper: port 38080 is busy. Another helper may already be running.");
        close(server); return 1;
    }
    char message[180];
    snprintf(message, sizeof message, "RemTeh Pair Helper: %s\nEnter this code on Switch. Valid for 5 minutes. Then use PS5 Remote Play > Link Device.", code);
    notify(message);
    puts("RemTeh Pair Helper 0.1.0 listening; no account IDs or codes logged.");
    fflush(stdout);
    int attempts = 0;
    const int64_t deadline = now_ms() + (int64_t)ttl * 1000;
    while (now_ms() < deadline && attempts < MAX_ATTEMPTS) {
        struct pollfd pollfd = { .fd = server, .events = POLLIN };
        if (poll(&pollfd, 1, 250) <= 0) continue;
        struct sockaddr_in peer;
        socklen_t length = sizeof peer;
        int fd = accept(server, (struct sockaddr *)&peer, &length);
        if (fd < 0) continue;
        struct timeval timeout = { .tv_sec = 2 };
        setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof timeout);
        if (!permitted_peer(&peer)) { close(fd); continue; }
        char body[9] = {0};
        int request = read_request(fd, body, deadline);
        bool done = false;
        if (now_ms() >= deadline) reply(fd, 410, "{\"error\":\"expired\"}");
        else if (request == 0) reply(fd, 200, "{\"protocol\":1,\"version\":\"0.1.0\",\"pairingRequired\":true}");
        else if (request < 0) reply(fd, 400, "{\"error\":\"invalid_request\"}");
        else {
            unsigned difference = 0;
            for (int i = 0; i < 8; ++i) difference |= (unsigned)(code[i] ^ body[i]);
            if (difference) { attempts++; reply(fd, 401, "{\"error\":\"wrong_code\"}"); }
            else {
                int current_user;
                uint8_t current_account[8];
                if (active_account(&current_user, current_account) || current_user != user || memcmp(account, current_account, 8)) {
                    reply(fd, 409, "{\"error\":\"profile_changed_restart_helper\"}");
                    done = true;
                } else {
                    char encoded[13], response[150];
                    base64_account(account, encoded);
                    snprintf(response, sizeof response, "{\"protocol\":1,\"version\":\"0.1.0\",\"accountId\":\"%s\"}", encoded);
                    reply(fd, 200, response);
                    done = true;
                    notify("RemTeh: profile sent to Switch. Now open Remote Play > Link Device on PS5.");
                }
            }
        }
        close(fd);
        if (done) break;
    }
    close(server);
    memset(account, 0, sizeof account); memset(code, 0, sizeof code);
    puts("RemTeh Pair Helper stopped.");
    return 0;
}
