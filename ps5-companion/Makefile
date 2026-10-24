# SPDX-License-Identifier: GPL-3.0-or-later
ifdef PS5_PAYLOAD_SDK
include $(PS5_PAYLOAD_SDK)/toolchain/prospero.mk
else
$(error Set PS5_PAYLOAD_SDK to the open-source ps5-payload-sdk directory)
endif
CFLAGS := -O2 -Wall -Wextra -Werror -std=c11
all: remteh-pair-helper.elf
remteh-pair-helper.elf: main.c
	$(CC) $(CFLAGS) -o $@ $< -lSceUserService -lSceRegMgr
