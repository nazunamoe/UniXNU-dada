// SPDX-License-Identifier: BSD-2-Clause-Patent
//
// dada glue for the OnePlus 13T Stage 7 display path (NativeLegacyDisplay, NativeGOPPresenter, DpuProbe, Stage7Probe and
// NativeKeyStoreEvents from UniXNU-Pagani-Drivers c888efd).
//
// The 13T links those objects against its BootProgress overlay, which owns the framebuffer while the kernel boots and yields
// it to the system frames. dada builds no BootProgress (CONFIG_XNU_BOOT_PROGRESS=n), so this file supplies the interface of
// drivers/BootProgress/PeripheralStatus.h:
//  - status lines go to the kernel message buffer, which dada's UFS boot log (dada-log=1) already captures;
//  - the display handoff turns XNU's own video console off (kPEDisableScreen), so verbose text no longer draws over the
//    frames the display copies into the GOP framebuffer. A failed first copy turns it back on;
//  - the per-frame counters, rows and rings of the overlay are no-ops.
// Every definition is weak, so a later BootProgress build of this board replaces it as a whole.
// pagani_panel_set_power is the 13T DSI panel's power hook; dada has no panel driver yet, so it only records the request.
#include <IOKit/IOLib.h>
#include <pexpert/pexpert.h>
#include "../BootProgress/PeripheralStatus.h"

#define DADA_WEAK extern "C" __attribute__((weak))

static volatile uint32_t dadaConsoleHandedOff;
static volatile uint64_t dadaDisplayFrames;
static volatile uint32_t dadaPanelPower=~0u;

DADA_WEAK int boot_progress_display_handoff(void) {
    if (!__atomic_exchange_n(&dadaConsoleHandedOff,1,__ATOMIC_ACQ_REL)) {
        printf("dada-display: handoff, video console off\n");
        PE_initialize_console(nullptr,kPEDisableScreen);
    }
    return 1;
}
DADA_WEAK void boot_progress_display_failed(void) {
    if (__atomic_exchange_n(&dadaConsoleHandedOff,0,__ATOMIC_ACQ_REL)) {
        printf("dada-display: first copy failed, video console back on\n");
        PE_initialize_console(nullptr,kPEEnableScreen);
    }
}
DADA_WEAK void boot_progress_display_status(const char *detail,uint64_t value) {
    printf("dada-display: %s 0x%llx\n",detail?detail:"?",(unsigned long long)value);
}
DADA_WEAK void boot_progress_peripheral_enable(int) {}
DADA_WEAK void boot_progress_platform_enable(int) {}
DADA_WEAK void boot_progress_peripheral(unsigned device,const char *stage,int32_t result,uint32_t,uint64_t) {
    if (result) printf("dada-display: peripheral %u %s 0x%x\n",device,stage?stage:"?",(uint32_t)result);
}
DADA_WEAK void boot_progress_peripheral_frame(void) {}
DADA_WEAK void boot_progress_display_frames(uint64_t frames) {dadaDisplayFrames=frames;}
DADA_WEAK void boot_progress_frame(unsigned,uint64_t) {}
DADA_WEAK void boot_progress_frame_timed(unsigned,uint64_t,const struct pagani_frame_timing *) {}
DADA_WEAK void boot_progress_frame_stage(unsigned,uint64_t) {}
DADA_WEAK void boot_progress_display_event(unsigned) {}
DADA_WEAK void boot_progress_trace(const char *text) {if (text) printf("dada-display: %s\n",text);}
DADA_WEAK void boot_progress_trace_values(const char *label,uint64_t a,uint64_t b) {
    printf("dada-display: %s 0x%llx 0x%llx\n",label?label:"?",(unsigned long long)a,(unsigned long long)b);
}
DADA_WEAK int boot_progress_trace_enabled(void) {return 0;}
DADA_WEAK void pagani_panel_set_power(unsigned ordinal) {
    if (__atomic_exchange_n(&dadaPanelPower,ordinal,__ATOMIC_RELAXED)!=ordinal)
        printf("dada-display: panel power state %u requested (no dada panel driver)\n",ordinal);
}
